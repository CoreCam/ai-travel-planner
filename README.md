🌍 AI Travel Planner - Production Ready
A streamlined AI-powered travel planning application with real flight booking and car rental integration.

✨ Features
Real Flight Search: Live flight data from Kiwi.com API via RapidAPI
Working Booking Links: Direct integration with Skyscanner for flights and car rentals
Time Preferences: Morning, afternoon, evening, and late night flight filtering
Restaurant Recommendations: AI-powered dining suggestions with business details
Elegant Design: Professional black, white, and mustard gold theme with consistent styling
Persistent State: Travel plans stay visible without page refreshes
Streamlined Experience: Fast, clean interface without unnecessary API dependencies
🚀 Quick Start
Prerequisites
Python 3.8+
Streamlit
API Keys (see Configuration section)
Installation
Clone/Download this folder to your local machine

Install Dependencies:

pip install -r requirements.txt
Set Up Environment Variables (see Configuration section below)

Run the Application:

streamlit run travelagent.py
🔧 Configuration
Create a .env file in the project root with your API keys:

# Required APIs
RAPIDAPI_KEY=your_rapidapi_key_here
GOOGLE_PLACES_API_KEY=your_google_places_key_here
GOOGLE_API_KEY=your_google_ai_key_here
SERPAPI_API_KEY=your_serpapi_key_here

# Optional (for enhanced features)
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
API Key Sources
RapidAPI Key (Required for flights): https://rapidapi.com/

Subscribe to "Cheap Flight Search" by Sky-scanneR team
Google Places API (Required for restaurants): Google Cloud Console

Enable Places API
Google AI API (Required for AI recommendations): Google AI Studio

SerpAPI (Required for restaurant search): https://serpapi.com/

🛫 How It Works
Flight Booking
Search: Real-time flight data from Kiwi.com via RapidAPI
Filter: Time preferences and traveler count
Book: Direct links to Skyscanner with pre-filled search parameters
Car Rental Booking
Integration: Uses Skyscanner's car hire system
Consistency: Same trusted platform as flight booking
Format: Correct Skyscanner car hire URL structure
URL Formats
Flights: https://www.skyscanner.com/transport/flights/{origin}/{destination}/{departure}/{return}/?adults={travelers}
Car Hire: https://www.skyscanner.com/carhire/results/{location}/{location}/{pickup_datetime}/{dropoff_datetime}/30/
📁 Project Structure
GenAI_Travel_Planner_Clean/
├── travelagent.py          # Main Streamlit application
├── config.py               # Configuration and API key management
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── .env                   # API keys (create this file)
🎨 Features Breakdown
Core Functionality
✅ Real flight search with prices and times
✅ Working Skyscanner booking links (flights & cars)
✅ Time preference filtering
✅ Restaurant recommendations with business details
✅ Responsive UI with travel-themed design
Technical Highlights
API Optimization: Removed unnecessary paid APIs
Direct Booking: No intermediary steps, direct to booking platforms
Error Handling: Graceful fallbacks and user-friendly messages
Performance: Fast loading with minimal API calls
🌟 Success Metrics
✅ Working Flight Booking: Tested and confirmed working
✅ Working Car Rental: Tested and confirmed working
✅ Clean Interface: Streamlined user experience
✅ Production Ready: Optimized for deployment
🔧 Troubleshooting
Common Issues
"No flights found": Check API keys and internet connection
Booking links not working: Verify Skyscanner URL format
Restaurant recommendations empty: Check Google Places API quota
Debug Mode
Set DEBUG=True in config.py to enable detailed logging.

📞 Support
For issues or questions:

Check the troubleshooting section above
Verify all API keys are correctly configured
Ensure all dependencies are installed
🎯 Ready for Production
This version has been optimized and tested with:

Working flight booking via Skyscanner
Working car rental booking via Skyscanner
Streamlined API usage
Clean, professional interface
Reliable error handling
Perfect for deployment to Streamlit Cloud, Heroku, or any Python hosting platform!
