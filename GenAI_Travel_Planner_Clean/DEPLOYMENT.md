# 🚀 Deployment Guide

## Quick Deployment Steps

### 1. Prepare Repository
```bash
# Navigate to your travel agent folder
cd GenAI_Travel_Panner_AI_Agent

# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: AI Travel Planner"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/ai-travel-planner.git
git branch -M main
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**
2. **Sign in with GitHub**
3. **Click "New app"**
4. **Select your repository**: `yourusername/ai-travel-planner`
5. **Main file path**: `travelagent.py`
6. **Click "Advanced settings"**
7. **Add your secrets** in the secrets section:

```toml
[secrets]
OPENAI_API_KEY = "your_openai_api_key"
GOOGLE_API_KEY = "your_google_api_key" 
GOOGLE_PLACES_API_KEY = "your_google_places_api_key"
AMADEUS_CLIENT_ID = "your_amadeus_client_id"
AMADEUS_CLIENT_SECRET = "your_amadeus_client_secret"
SERPAPI_KEY = "your_serpapi_key"
```

8. **Click "Deploy!"**

### 3. Alternative: Deploy on Railway

1. **Go to [railway.app](https://railway.app)**
2. **Connect GitHub repository**
3. **Add environment variables**
4. **Deploy automatically**

### 4. Alternative: Deploy on Heroku

1. **Install Heroku CLI**
2. **Login**: `heroku login`
3. **Create app**: `heroku create your-app-name`
4. **Set environment variables**:
```bash
heroku config:set OPENAI_API_KEY=your_key
heroku config:set GOOGLE_API_KEY=your_key
heroku config:set GOOGLE_PLACES_API_KEY=your_key
heroku config:set AMADEUS_CLIENT_ID=your_key
heroku config:set AMADEUS_CLIENT_SECRET=your_key
heroku config:set SERPAPI_KEY=your_key
```
5. **Deploy**: `git push heroku main`

## 🔑 Getting API Keys

### OpenAI
- Go to: https://platform.openai.com/api-keys
- Create new secret key
- Copy the key (starts with `sk-`)

### Google APIs
- Go to: https://console.cloud.google.com/
- Enable: Places API, Maps JavaScript API
- Create credentials → API Key
- Restrict key to your domains

### Amadeus
- Go to: https://developers.amadeus.com/
- Create account → Get API Key
- Copy Client ID and Client Secret

### SerpAPI (Optional)
- Go to: https://serpapi.com/
- Sign up → Get API Key
- Copy the key

## ✅ Deployment Checklist

- [ ] All API keys obtained and tested
- [ ] Repository pushed to GitHub
- [ ] .env file NOT committed (check .gitignore)
- [ ] requirements.txt includes all dependencies
- [ ] Runtime.txt specifies Python version
- [ ] Secrets configured in deployment platform
- [ ] App deployed and accessible
- [ ] All features tested in production

## 🆘 Troubleshooting

**App won't start?**
- Check that all required API keys are set
- Verify Python version compatibility
- Check deployment logs for errors

**API errors?**
- Verify API keys are correct and active
- Check API quotas and billing
- Ensure keys have proper permissions

**Missing features?**
- Check if optional APIs (SerpAPI) are configured
- Verify all dependencies are installed

## 🎉 Success!
Your AI Travel Planner is now live and ready to help users plan amazing trips! 🌍✈️
