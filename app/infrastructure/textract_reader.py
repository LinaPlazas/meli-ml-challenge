import boto3

class TextractReader:
    def __init__(self, region_name: str = "us-east-1"):
        self.textract = boto3.client("textract", region_name=region_name)

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        response = self.textract.analyze_document(
            Document={"Bytes": file_bytes},
            FeatureTypes=["TABLES", "FORMS"]
        )

        text = ""
        for block in response["Blocks"]:
            if block["BlockType"] == "LINE":
                text += " " + block["Text"]
        return text
