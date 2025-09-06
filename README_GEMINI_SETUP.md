# OceanScope Configuration Guide

## Setting up Environment Variables

### Method 1: Using .env File (Recommended)

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Get a Gemini API Key**:
   - Go to [Google AI Studio](https://ai.google.dev/)
   - Create an account or sign in
   - Generate an API key

3. **Configure your .env file**:
   - Open `.env` in a text editor
   - Replace `your_gemini_api_key_here` with your actual API key
   - Optionally adjust other settings

   Example `.env` file:
   ```env
   GEMINI_API_KEY=AIzaSyC1234567890abcdef...
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_TEMPERATURE=0.7
   DEBUG=false
   ```

### Method 2: Using Streamlit Secrets (Alternative)

1. **Edit `.streamlit/secrets.toml`**:
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   ```

### Method 3: System Environment Variables

**Windows (PowerShell)**:
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**Linux/Mac**:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env file with your API key

# Run the application
streamlit run app.py
```

## Environment Variables Reference

| Variable | Description | Default Value           |
|----------|-------------|-------------------------|
| `GEMINI_API_KEY` | Your Gemini API key | Required                |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash`      |
| `GEMINI_TEMPERATURE` | Response creativity (0.0-1.0) | `0.7`                   |
| `GEMINI_MAX_TOKENS` | Maximum response length | `1000`                  |
| `DATA_FILE_PATH` | Path to NetCDF data file | `data/20250101_prof.nc` |
| `MAX_PROFILES_DISPLAY` | Max profiles to show in UI | `100`                   |
| `DEBUG` | Enable debug mode | `false`                 |
| `CACHE_ENABLED` | Enable data caching | `true`                  |
| `LOG_LEVEL` | Logging level | `INFO`                  |

## Features

- **Enhanced AI Responses**: Natural language answers powered by Gemini LLM
- **Data Visualization**: Interactive matplotlib plots
- **Ocean Data Analysis**: Comprehensive statistics and insights
- **Robust Error Handling**: Graceful fallbacks when API is unavailable

## Usage Tips

- Ask questions like:
  - "What can you tell me about the temperature profile?"
  - "How does salinity change with depth?"
  - "What are the characteristics of this ocean profile?"
  - "Analyze the water mass properties"

## Troubleshooting

### API Key Issues
- If you see "Gemini API key not found":
  1. Check your `.env` file exists and contains `GEMINI_API_KEY=your_actual_key`
  2. Ensure there are no quotes around the key in `.env` file
  3. Verify the API key is valid at [Google AI Studio](https://ai.google.dev/)
  4. Restart the Streamlit application after making changes

### Environment Variables Not Loading
- Ensure `.env` file is in the project root directory (same level as `app.py`)
- Check file permissions - the `.env` file should be readable
- Verify `python-dotenv` is installed: `pip install python-dotenv`

### General Issues
- The app will work with limited functionality even without the API key
- Check the console for any error messages during startup
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Security Notes
- Never commit your `.env` file to version control
- The `.env` file is included in `.gitignore` for security
- Use `.env.example` as a template for sharing configuration structure