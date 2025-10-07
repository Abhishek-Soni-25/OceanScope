# 🌊 Unified Ocean Data Platform

> **An AI-powered platform built with Streamlit that unifies global ocean datasets through ETL, Retrieval-Augmented Generation (RAG), and intelligent search using FAISS and Ollama.**

---

## 📘 Overview

The **Unified Ocean Data Platform** is an end-to-end intelligent system designed to integrate, process, and analyze oceanographic data from multiple official sources — including **ARGO floats**, **BGC floats**, **satellite observations**, and **marine datasets**.  

This platform enables users to **query, visualize, and understand ocean data interactively** through a conversational interface powered by **RAG**, **FAISS**, and **Ollama**, while maintaining a seamless user experience via login and chat history management.

---

## 🔁 Workflow

1. **Web Scraping:**  
   Data is automatically fetched from official sources such as ARGO, BGC, marine repositories, and satellite observation platforms.

2. **Local Storage:**  
   The raw data is first stored locally on the system for pre-processing.

3. **ETL Pipeline (Extract–Transform–Load):**  
   - **Extract:** Relevant parameters (e.g., temperature, salinity, pressure, chlorophyll) are extracted.  
   - **Transform:** Data is cleaned, standardized, and structured for database insertion.  
   - **Load:** Processed data is stored in the **PostgreSQL** database.

4. **Database Management:**  
   PostgreSQL serves as the central storage layer for structured ocean data, enabling efficient retrieval and querying.

5. **Vectorization & RAG:**  
   - Ocean dataset summaries and metadata are **vectorized** and indexed using **FAISS**.  
   - **Ollama** (LLM integration) is used to implement **Retrieval-Augmented Generation (RAG)**, allowing natural language queries that pull contextually relevant data directly from the database.

6. **User Interaction:**  
   - Users can **log in or sign up**, enabling personalized experiences and chat history tracking.  
   - A conversational interface allows users to **ask questions about ocean conditions**, visualize data, and retrieve insights interactively.

---

## 🚀 Key Features

- 🌐 **Unified Multi-Source Integration:** Combines ARGO, BGC, satellite, and marine data into one analytical environment.  
- ⚙️ **Automated ETL Pipeline:** End-to-end extraction, cleaning, transformation, and storage of data.  
- 🧠 **RAG-Enhanced Intelligence:** Combines structured queries with LLM-powered reasoning for intelligent responses.  
- 🧩 **FAISS Vector Database:** Enables semantic search and efficient retrieval of ocean-related information.  
- 💾 **PostgreSQL Backend:** Secure, scalable, and optimized for large ocean datasets.  
- 🔐 **User Authentication:** Login/signup system with personalized chat history retention.  
- 📊 **Interactive Visualizations:** Explore data through dynamic charts, maps, and profile plots within Streamlit.  
- 💬 **Conversational Interface:** Ask questions like *“Show me the temperature trend near the Indian Ocean”* — and get real-time, visual answers.  

---

## 🧠 System Architecture

The platform follows a modular and scalable architecture:

1. **Data Layer:** Web scrapers + ETL pipeline to gather and process raw data.  
2. **Storage Layer:** PostgreSQL for structured data + FAISS for vector storage.  
3. **Application Layer:** Streamlit web app providing UI, visualizations, and chat interface.  
4. **AI Layer:** Ollama-backed RAG pipeline for context-aware retrieval and responses.  
5. **Authentication Layer:** User management and chat session storage for personalized experiences.

---

## ⚙️ Tech Stack

| Layer | Technologies |
|-------|---------------|
| **Frontend & App** | Streamlit |
| **Database** | PostgreSQL |
| **Vector Search** | FAISS |
| **LLM Integration** | Ollama |
| **Data Handling** | Pandas, NumPy, Xarray |
| **Visualization** | Plotly, Matplotlib, Seaborn |
| **Web Scraping** | Requests, BeautifulSoup, Selenium |
| **ETL & Automation** | Custom Python Pipelines |
| **Authentication** | Streamlit Authentication + PostgreSQL |
| **AI Pipeline** | Retrieval-Augmented Generation (RAG) |

---

## 📊 Core Functionalities

- 🌡️ **Temperature–Salinity (T–S) Diagrams**  
- 🧩 **Vertical Profiles (Depth vs. Temperature/Salinity)**  
- 🗺️ **Float Path Maps and Satellite Overlays**  
- 📈 **Time Series Analysis**  
- 🔍 **RAG-based Query Search** — Ask domain-specific ocean questions and get AI-generated insights  
- 📑 **User Chat History** — Retrieve and revisit past analyses and visualizations  

---

## 🔮 Future Roadmap

- 🌍 Integration with **real-time sensor networks and IoT buoys**  
- 🤖 Advanced **forecasting models** for ocean temperature and salinity prediction  
- 🛰️ **Enhanced satellite data layers** (SST, chlorophyll, wave height)  
- 🔔 **Automated ocean alerts** for anomalies and climatic events  
- 📱 Mobile and API-based access for researchers and policy teams  

---

## 💡 Vision

The **Unified Ocean Data Platform** aims to transform how ocean information is accessed and understood — by unifying scattered datasets, infusing them with AI, and enabling **interactive, conversational, and data-driven exploration** of our oceans.

---
