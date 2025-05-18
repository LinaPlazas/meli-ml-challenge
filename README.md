<h1 align="center">Meli ML Chanllenge 🚀 </h1> 

## Resumen: 
El presente proyecto tiene como fin plantear una posible solución para el reto técnico planteado, el cual consiste en diseñar y construir un sistema que realice las siguientes tareas a partir de diferentes documentos en formato pdf:<br> 

***1. Clasificación automática por tipo de documento:*** <br>

   Cada archivo debe ser clasificado en una de las siguientes categorias: 
   - Contrato
   - Resolución
   - Certificado
   - Factura
2. **Detección de datos sensibles (PII)**
     
Identifica y resalta información confidencial como:
- Nombres completos  
- Números de identificación  
- Correos electrónicos  
- Teléfonos  
- Direcciones
  
3. **Identificación de documentos duplicados o similares**
  
Detecta documentos duplicados por medio de un checksum MD5.

4. **Segmentación y extracción de secciones de interés (Opcional)**

Extrae de cada documento la sección específica que contiene requisitos normativos,  
cuando exista, o marca el documento como “No Aplica”.

## Arquitectura y diseño de la solución: 
   El siguiente diagrama resume como está construida la presente solución:
   
