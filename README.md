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

## Arquitectura y diseño de la solución

El siguiente diagrama resume cómo está construida la presente solución:

![Arquitectura](images/Arquitectura.png)

### Desarrollo y construcción de la aplicación 

La aplicación fue desarrollada en FastAPI y luego construida como una imagen de docker la cual se almacena en Amazon ECR para su posterior despliegue.

  
### Despliegue de la aplicación 

En cuanto al despliegue se utilizó AWS ECS con Fargate como servicio de orquestación para ejecutar la imagen en un entorno serverless, asimismo se utilizó un Load Balancer que permite el acceso externo a la API.

### Servicios externos conectados 

Se utiliza MongoDB como base de datos para almacenar el texto extraído de los documentos, así como otros procesamientos realizados (clasificación de documentos, extracción de PII, información de duplicados, extracción de secciones de interés).

Por otro lado, también se cuenta con un bucket de S3 para almacenar los documentos utilizados tanto en el entrenamiento del modelo, que se describe más adelante, como en las diferentes pruebas de la aplicación.

## Implementación detallada de la solución

Para el desarrollo de la aplicación, se procuró seguir principios de arquitectura limpia, organizando el proyecto en módulos con responsabilidades definidas. A continuación se explicara cada uno de los modulos:

### Extracción de texto 
Para abordar el problema planteado, el primer paso realizado fue lograr la extracción de texto de archivos pdf, para esto se utilizó amazon textract debido a que ofrece una extracción robusta basada en machine learning,que no solo reconoce texto impreso, sino también estructuras complejas como tablas y formularios.

De igual manera para enfrentar el problema de el procesamiento asincronico se utilizo start_document_text_detection, esta opción permite iniciar múltiples procesos de extracción en paralelo sin necesidad de esperar a que cada uno finalice antes de continuar con el siguiente.

Para gestionar este procesamiento concurrente, se implementó una estrategia que permite lanzar varios trabajos de análisis al mismo tiempo, hacer seguimiento de cada uno de ellos de forma no bloqueante, y finalmente recolectar los resultados una vez completados. Una vez obtenidos los textos de los archivos pdf, se almacenan en la base de datos, lo que permite su posterior uso en tareas como clasificación automática, detección de información sensible o análisis de secciones normativas.

### Clasificación en categorias

#### Pre procesamiento y entrenamiento del modelo

Con el fin de implementar el sistema clasificador de textos, fueron necesarios unos pasos previos al desarrollo del modulo. En primer lugar se recolectaron diferentes archivos pdf con el objetivo de armar un dataset, de esta manera los documentos referentes a contratos, resoluciones y certificados, se obtuvieron del repositorio de datos abiertos de Secop II [Datos abiertos Secop II](https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-II-Contratos-Electr-nicos/jbjy-vk9h/about_data), de igual manera para las facturas, se utilizaron plantillas de ejemplo.

En total se obtuvieron la siguiente cantidad de documentos, la cantidad de paginas variaba por documento, algunos tenian hasta 15 páginas:

Certificados: 49 <br>
Contratos:43 <br>
Resoluciones: 56 <br>
Facturas: 37 <br>

Una vez recolectados los documentos de entrenamiento, se procedió a construir el dataset en formato tabular, con el fin de utilizarlo como entrada para los modelos,Este proceso se llevó a cabo mediante un notebook de Jupyter, ubicado en la ruta notebooks/create_tabular_dataset.py, la salida fue un archivo CSV que contiene los campos: filename, label (etiqueta correspondiente a la clase del documento) y text (texto extraído del PDF utilizando Amazon Textract) y se encuentra en la ruta notebooks/data/dataset.csv

Una vez obtenido el dataset tabular, se procedió a realizar diferentes pruebas utilizando modelos de aprendizaje automático tradicional. Para ello, se implementó una etapa de vectorización del texto puesto que  Los modelos no entienden palabras directamente, por lo cual la vectorización convierte el texto en representaciones numéricas que los algoritmos de machine learning pueden procesar. Se inició con un modelo de regresión logística debido a su simplicidad y buen desempeño en problemas de clasificación de texto. Los datos se dividieron en un 80 % para entrenamiento y un 20 % para validación. A continuación, se presentan los resultados obtenidos:

![matrizrl1](images/mc_regresion1.png)
![metricas1](images/metricas_regresion1.png)

Aunque los resultados fueron prometedores, se decidió mejorar el preprocesamiento del texto incorporando una pequeña etapa de limpieza y tokenización del texto para optimizar la calidad de las características extraídas. Además se decidió evaluar varios modelos de clasificación como adicional a la regresión logistica como Lineal SVM, Random Forest, Multinomial Naive Bayes, con el fin de comparar y elegir el que brindara mejores métricas. A continuación se muestran los resultados de cada uno de los modelos con la limpieza de texto realizada

Regresión Logistica
![matrizrl2](images/mc_regresion2.png)
![metricas2](images/metricas_regresion2.png)

SVM
![matrizsvm](images/mc_SVM.png)
![metricas3](images/metricas_SVM.png)

Random Forest
![matrizrandom](images/mc_randomforest.png)
![metricas4](images/metricas_randomforest.png)

NB
![matriznb](images/mc_NB.png)
![metricas1](images/metricas_NB.png)

Como se puede observar, en términos generales y para todas las métricas (Accuracy, Precision, Recall y F1-score), el modelo Random Forest alcanzó un desempeño cercano al 97%. Por ello, fue seleccionado para su implementación en el módulo de clasificación de categorías.

#### Implementación modulo clasificador

Una vez obtenido el modelo clasificador, se desarrolló el módulo encargado de determinar la categoría que mejor se ajusta al documento. Para ello, se consulta en la base de datos el texto extraído de los PDFs y se realiza la clasificación correspondiente. Finalmente, el módulo almacena dos campos: la categoría asignada y los scores, es decir, los puntajes de probabilidad asociados a cada una de las categorías.
   
