# survivor/services/football_api.py
import requests
import time
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class FootballDataAPI:
    """Service class for interacting with football-data.org API"""
    
    def __init__(self):
        self.api_key = settings.FOOTBALL_DATA_API_KEY
        self.base_url = settings.FOOTBALL_DATA_BASE_URL
        self.headers = {
            'X-Auth-Token': self.api_key
        }
        self.competition_id = 2002  # Bundesliga ID
        
    def _make_request(self, endpoint, params=None):
        """Make API request with rate limiting and error handling"""
        
        # Check rate limit
        self._check_rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # Record this request for rate limiting
            self._record_request()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(60)  # Wait a minute
                return self._make_request(endpoint, params)  # Retry
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def _check_rate_limit(self):
        """Simple rate limiting using Django cache"""
        cache_key = 'api_requests_count'
        count = cache.get(cache_key, 0)
        
        if count >= settings.API_RATE_LIMIT:
            # Wait until rate limit resets
            logger.info("Rate limit reached, waiting...")
            time.sleep(60)
            cache.set(cache_key, 0, settings.API_RATE_PERIOD)
    
    def _record_request(self):
        """Record API request for rate limiting"""
        cache_key = 'api_requests_count'
        count = cache.get(cache_key, 0)
        cache.set(cache_key, count + 1, settings.API_RATE_PERIOD)
    
    def get_teams(self):
        """Get all teams in Bundesliga"""
        endpoint = f"competitions/{self.competition_id}/teams"
        data = self._make_request(endpoint)
        
        if data and 'teams' in data:
            return data['teams']
        return []
    
    def get_current_season(self):
        """Get current season information"""
        endpoint = f"competitions/{self.competition_id}"
        data = self._make_request(endpoint)
        
        if data:
            return data.get('currentSeason', {})
        return {}
    
    def get_matches(self, season=None, matchday=None):
        """Get matches for current season or specific matchday"""
        endpoint = f"competitions/{self.competition_id}/matches"
        params = {}
        
        if season:
            params['season'] = season
        if matchday:
            params['matchday'] = matchday
            
        data = self._make_request(endpoint, params)
        
        if data and 'matches' in data:
            return data['matches']
        return []
    
    def get_standings(self):
        """Get current league standings"""
        endpoint = f"competitions/{self.competition_id}/standings"
        data = self._make_request(endpoint)
        
        if data and 'standings' in data:
            return data['standings']
        return []
    
    def get_match_details(self, match_id):
        """Get details for a specific match"""
        endpoint = f"matches/{match_id}"
        return self._make_request(endpoint)


class TeamMapper:
    """Maps API team names to our database team names"""
    
    # Mapping between football-data.org names and our database names
    # You might need to adjust these based on exact API responses
    TEAM_MAPPINGS = {
        'FC Bayern München': 'Bayern Munich',
        'Borussia Dortmund': 'Borussia Dortmund',
        'Bayer 04 Leverkusen': 'Bayer Leverkusen',
        'RB Leipzig': 'RB Leipzig',
        '1. FC Union Berlin': 'Union Berlin',
        'Sport-Club Freiburg': 'SC Freiburg',
        'Eintracht Frankfurt': 'Eintracht Frankfurt',
        'VfL Wolfsburg': 'VfL Wolfsburg',
        '1. FSV Mainz 05': 'Mainz 05',
        'Borussia Mönchengladbach': 'Borussia Mönchengladbach',
        '1. FC Köln': 'FC Köln',
        'TSG 1899 Hoffenheim': 'Hoffenheim',
        'SV Werder Bremen': 'Werder Bremen',
        'FC Augsburg': 'FC Augsburg',
        'VfB Stuttgart': 'VfB Stuttgart',
        'VfL Bochum 1848': 'VfL Bochum',
        '1. FC Heidenheim 1846': 'FC Heidenheim',
        'SV Darmstadt 98': 'SV Darmstadt 98',
        # Add any new teams or adjust as needed
    }
    
    @classmethod
    def get_team_name(cls, api_name):
        """Convert API team name to our database team name"""
        return cls.TEAM_MAPPINGS.get(api_name, api_name)
    
    @classmethod
    def get_api_name(cls, db_name):
        """Convert our database team name to API team name"""
        # Reverse mapping
        for api_name, mapped_name in cls.TEAM_MAPPINGS.items():
            if mapped_name == db_name:
                return api_name
        return db_name