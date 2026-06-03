# Deployment Guide

## Option 1: Streamlit Cloud (Easiest)

### Steps:
1. Push your code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. Go to [Streamlit Cloud](https://share.streamlit.io)

3. Click "New app" and:
   - Connect your GitHub repository
   - Select the repository
   - Branch: main
   - Main file path: app.py

4. Click "Deploy"

## Option 2: Docker Deployment

### Build Docker Image:
```bash
docker build -t ai-trading-software .
```

### Run Docker Container:
```bash
docker run -p 8501:8501 ai-trading-software
```

### Access the App:
Open browser at http://localhost:8501

### Push to Docker Hub (Optional):
```bash
docker tag ai-trading-software your-dockerhub-username/ai-trading-software
docker push your-dockerhub-username/ai-trading-software
```

## Option 3: Heroku Deployment

### Prerequisites:
- Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

### Deploy Commands:
```bash
# Login to Heroku
heroku login

# Create a new Heroku app
heroku create ai-trading-software

# Set buildpack to Python
heroku buildpacks:set heroku/python

# Deploy to Heroku
git push heroku main

# Open the deployed app
heroku open
```

### View Logs:
```bash
heroku logs --tail
```

## Option 4: Local Deployment

### Install Dependencies:
```bash
pip install -r requirements.txt
```

### Run the App:
```bash
streamlit run app.py
```

Or using Python:
```bash
python -m streamlit run app.py
```

## Environment Variables (Optional)

You can set these environment variables for configuration:

- `STREAMLIT_SERVER_PORT`: Port number (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)

## Troubleshooting

### Streamlit Cloud Issues:
- Ensure all dependencies are in requirements.txt
- Check that app.py is in the root directory
- Verify GitHub repository is public or you have proper authentication

### Docker Issues:
- Ensure Docker is running: `docker ps`
- Check logs: `docker logs <container-id>`
- Rebuild image if dependencies change

### Heroku Issues:
- Check logs: `heroku logs --tail`
- Verify buildpack is set: `heroku buildpacks`
- Ensure runtime.txt is present

## Post-Deployment Checklist

- [ ] App loads successfully
- [ ] All features work (analysis, portfolio, backtesting)
- [ ] Export functionality works (if dependencies installed)
- [ ] Auto-refresh works on charts
- [ ] No console errors
- [ ] Responsive design works on mobile

## Security Notes

- For production, add authentication
- Consider adding rate limiting
- Use environment variables for sensitive data
- Enable HTTPS (automatic on Streamlit Cloud and Heroku)
