import re
import os
from app.config.db import MongoDB
from app.exceptions.custom_exceptions import NormativeSectionError

class NormativeSectionService:
    def __init__(self):
        self.db = MongoDB()
        self.prefix = os.getenv("S3_PREFIX", "uploads/")
        self.pattern = r"""(
        (?:
            (de\s+acuerdo\s+con|
             en\s+conformidad\s+con|
             cumpliendo\s+con|
             siguiendo\s+los\s+lineamientos\s+de|
             conforme\s+a|
             estará\s+sujeto\s+a\s+lo\s+dispuesto\s+en|
             que\s+en\s+virtud\s+del|
             en\s+cumplimiento\s+del|
             según\s+la|
             de\s+conformidad\s+con|
             reforma\s+de\s+los\s+artículos|
             incluyendo\s+los\s+fondos\s+establecidos\s+en)
            \s+)?
        (artículo(?:s)?\s+\d{1,4}(?:\s*(?:y|e|,)?\s*\d{1,4})*|
         ley\s+\d{3,4}(?:\s+de\s+\d{4})?|
         decreto\s+\d{3,4}(?:\s+de\s+\d{4})?|
         resolución\s+\d{3,4}(?:\s+de\s+\d{4})?|
         norma\s+(?:ISO)?\s*\d{3,5}(?::\d{4})?|
         normativa\s+vigente|
         regulación\s+establecida)
        .{0,100}?
        (?=\n|\r|\.|\Z)
    )"""

    async def extract_all_normative_sections(self) -> list[dict]:
        try:
            collection = self.db.document_analysis
            documents = await collection.find({}).to_list(None)
            final_results = []
            for doc in documents:
                result = await self._extract_and_update(doc)
                if result:
                    final_results.append(result)
            return final_results
        except Exception as e:
            raise Exception(f"Unexpected error during normative section extraction: {str(e)}")

    async def _extract_and_update(self, doc: dict) -> dict | None:
        try:
            filename = doc.get("filename")
            text = doc.get("text", "")
            normative_sections = self.extract_normative_sections(text)
            result_value = normative_sections if normative_sections else ["NA"]

            await self.db.document_analysis.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "normative_section": result_value
                }}
            )
            return {
                "filename": filename,
                "normative_section": result_value
            }
        except Exception as e:
            raise Exception(f"Error processing document {doc.get('filename')}: {str(e)}")

    def extract_normative_sections(self, text: str) -> list[str] | None:
        try:
            matches = re.findall(self.pattern, text, flags=re.IGNORECASE | re.VERBOSE)
            return [m[0].strip() for m in matches] if matches else None
        except Exception as e:
            raise Exception(f"Error extracting normative sections: {str(e)}")

    async def extract_normative_sections_by_filenames(self, filenames: list[str]) -> list[dict]:
        try:
            filenames_with_prefix = [
                f"{self.prefix}{filename}" if not filename.startswith(self.prefix) else filename
                for filename in filenames]
            collection = self.db.document_analysis
            documents = await collection.find({"filename": {"$in": filenames_with_prefix}}).to_list(None)
            found_filenames = {doc.get("filename") for doc in documents}
            final_results = []
            for doc in documents:
                try:
                    filename = doc.get("filename")
                    text = doc.get("text", "")
                    normative_sections = self.extract_normative_sections(text)
                    result_value = normative_sections if normative_sections else ["NA"]
                    await collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {
                            "normative_section": result_value
                        }}
                    )
                    final_results.append({
                        "filename": filename,
                        "normative_section": result_value,
                        "message": "Successfully extracted"
                    })
                except Exception as e:
                    final_results.append({
                        "filename": doc.get("filename"),
                        "normative_section": [],
                        "message": f"Skipped due to error: {str(e)}"
                    })
            missing_files = set(filenames_with_prefix) - found_filenames
            for missing_filename in missing_files:
                final_results.append({
                    "filename": missing_filename,
                    "normative_section": [],
                    "message": "File not found in the database"
                })
            return final_results

        except Exception as e:
            raise NormativeSectionError(detail=f"Unexpected error during normative section extraction: {str(e)}")
