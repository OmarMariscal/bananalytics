# 🍌📊 BanAnalytics 

![Python](https://img.shields.io/badge/Python-3.14.3-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.2-009688?style=for-the-badge&logo=fastapi)
![Flet](https://img.shields.io/badge/Flet-UI-ff4b4b?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=for-the-badge&logo=postgresql)
![Scikit-Learn](https://img.shields.io/badge/Machine_Learning-Scikit_Learn-F7931E?style=for-the-badge&logo=scikit-learn)

> **BanAnalytics** es una plataforma integral de análisis de datos empresariales. Diseñada con una arquitectura moderna de microservicios, combina una interfaz local eficiente, un backend seguro en la nube y motores de Inteligencia Artificial para predecir demanda y optimizar operaciones.

---

## 🏗️ Arquitectura del Sistema

El proyecto está diseñado bajo un modelo de **Monorepo** con separación estricta de responsabilidades. Se divide en tres módulos principales, cada uno con su propio entorno aislado:

* 🏪 **`cliente_local/` (Frontend):** Aplicación de escritorio desarrollada con **Flet**. Actúa como el recolector de datos y ofreciendo una interfaz fluida, rápida y amigable para el operador donde pueda visualizar todas las predicciones del modelo de IA.
* 🧠 **`api_gateway/` (Backend):** El núcleo del sistema desarrollado en **FastAPI**. Gestiona la lógica de negocio, la autenticación y la comunicación segura con nuestra base de datos PostgreSQL alojada en **Neon**.
* 🤖 **`worker_ml/` (Inteligencia Artificial):** Laboratorio de ciencia de datos. Utiliza **Pandas** y **Scikit-Learn** para procesar el historial de ventas y entrenar modelos predictivos que ayudan a la toma de decisiones.

---

## 🚀 Inicio Rápido (Desarrolladores)

Si eres un nuevo miembro del equipo o deseas probar el proyecto localmente, asegúrate de tener instalado **Python 3.12+** y sigue estos pasos:

1. **Clona el repositorio:**

       git clone https://github.com/OmarMariscal/bananalytics.git

2. **Lee las reglas del equipo:**
   Por favor, revisa estrictamente nuestro archivo [`CONTRIBUTING.md`](./CONTRIBUTING.md) para entender el flujo de trabajo (GitHub Flow) y la configuración de entornos virtuales por módulo.

3. **Configura tus variables de entorno:**
   Solicita al administrador las credenciales `.env` correspondientes para conectarte a la base de datos de desarrollo.

---

## 👨‍💻 Equipo de Desarrollo

Este proyecto ha sido diseñado y desarrollado por:

* **Mariscal Rodríguez Omar Jesús** - *Data Scientist (Machine Learning)* - [Enlace a su GitHub](https://github.com/OmarMariscal)
* **Nápoles Plascencia Rogelio** - *Frontend Developer (Flet)* - [Enlace a su GitHub](https://github.com/Rogelio-Napoles)
* **Rodríguez Guijarro Roberto Emiliano** - *Backend Developer (Python)* - [Enlace a su GitHub](https://github.com/emi-dev007)
* **Gómez Comparan Angel** - *Desarrollo de API REST y Base de Datos Postgre (Fast API)* - [Enlace a su GitHub](https://github.com/Enjeru-105)
---
*Desarrollado con pasión y buenas prácticas de Ingeniería de Software.* 🚀