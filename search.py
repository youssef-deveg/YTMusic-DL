"""
YouTube Data API v3 search module
Handles searching for videos, playlists, and retrieving video details
"""

import asyncio
from typing import List, Dict, Any, Optional
import httpx
from urllib.parse import quote

from config import (
    YOUTUBE_API_KEY, 
    YOUTUBE_API_BASE_URL, 
    SEARCH_SORT_OPTIONS,
    DURATION_FILTERS,
    VIDEO_TYPE_FILTERS
)
from utils import format_duration, parse_iso_datetime, format_views


class YouTubeSearcher:
    """YouTube Data API v3 search handler"""
    
    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
        self.base_url = YOUTUBE_API_BASE_URL
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def search(
        self,
        query: str,
        max_results: int = 25,
        order: str = "relevance",
        video_duration: str = "",
        video_type: str = "",
        add_audio_keyword: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search YouTube for videos
        
        Args:
            query: Search query
            max_results: Maximum number of results (max 50)
            order: Sort order (relevance, viewCount, date, rating)
            video_duration: Duration filter (short, medium, long)
            video_type: Type filter (video, playlist, channel)
            add_audio_keyword: Whether to append "audio" to query
        """
        if not query.strip():
            return []
        
        # Add audio keyword for music searches
        if add_audio_keyword and not query.lower().startswith('audio'):
            search_query = f"{query} audio"
        else:
            search_query = query
        
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'maxResults': min(max_results, 50),
            'key': self.api_key,
            'order': order
        }
        
        # Add filters
        if video_duration in ['short', 'medium', 'long']:
            params['videoDuration'] = video_duration
        
        if video_type == 'shorts':
            # For shorts, we'll filter later
            pass
        
        try:
            url = f"{self.base_url}/search"
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                print(f"YouTube API error: {error_msg}")
                return []
            
            items = data.get('items', [])
            
            # Extract video IDs
            video_ids = [item['id']['videoId'] for item in items if 'videoId' in item.get('id', {})]
            
            if not video_ids:
                return []
            
            # Get detailed video information
            video_details = await self._get_video_details(video_ids)
            
            # Combine search results with details
            results = []
            for item in items:
                video_id = item.get('id', {}).get('videoId')
                if video_id and video_id in video_details:
                    detail = video_details[video_id]
                    
                    # Check if it's a short
                    is_short = self._is_short_video(detail.get('duration', ''))
                    
                    # Filter by type if specified
                    if video_type == 'shorts' and not is_short:
                        continue
                    if video_type == 'video' and is_short:
                        continue
                    
                    result = {
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'channel': item['snippet']['channelTitle'],
                        'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', ''),
                        'thumbnail_high': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                        'description': item['snippet']['description'],
                        'published_at': item['snippet']['publishedAt'],
                        'duration': format_duration(detail.get('duration', '')),
                        'duration_raw': detail.get('duration', ''),
                        'views': int(detail.get('statistics', {}).get('viewCount', 0)),
                        'views_formatted': format_views(int(detail.get('statistics', {}).get('viewCount', 0))),
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'is_short': is_short
                    }
                    results.append(result)
            
            return results
            
        except httpx.HTTPError as e:
            print(f"HTTP error during search: {e}")
            return []
        except Exception as e:
            print(f"Error during search: {e}")
            return []
    
    async def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict]:
        """Get detailed information for multiple videos"""
        if not video_ids:
            return {}
        
        # API allows up to 50 IDs at once
        chunks = [video_ids[i:i+50] for i in range(0, len(video_ids), 50)]
        all_details = {}
        
        for chunk in chunks:
            params = {
                'part': 'contentDetails,statistics',
                'id': ','.join(chunk),
                'key': self.api_key
            }
            
            try:
                url = f"{self.base_url}/videos"
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    video_id = item['id']
                    all_details[video_id] = {
                        'duration': item.get('contentDetails', {}).get('duration', ''),
                        'statistics': item.get('statistics', {})
                    }
                    
            except Exception as e:
                print(f"Error fetching video details: {e}")
        
        return all_details
    
    def _is_short_video(self, duration: str) -> bool:
        """Check if video duration indicates it's a Short (< 60 seconds)"""
        if not duration:
            return False
        
        # Parse PT#M#S format
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return False
        
        hours, minutes, seconds = match.groups()
        total_seconds = (
            (int(hours) if hours else 0) * 3600 +
            (int(minutes) if minutes else 0) * 60 +
            (int(seconds) if seconds else 0)
        )
        
        return total_seconds <= 60
    
    async def get_playlist_videos(self, playlist_id: str) -> List[Dict[str, Any]]:
        """Get all videos from a playlist"""
        videos = []
        next_page_token = None
        
        while True:
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': 50,
                'key': self.api_key
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                url = f"{self.base_url}/playlistItems"
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                items = data.get('items', [])
                video_ids = []
                
                for item in items:
                    snippet = item.get('snippet', {})
                    resource = snippet.get('resourceId', {})
                    video_id = resource.get('videoId')
                    
                    if video_id:
                        video_ids.append(video_id)
                        videos.append({
                            'id': video_id,
                            'title': snippet.get('title', 'Unknown'),
                            'channel': snippet.get('videoOwnerChannelTitle', 'Unknown'),
                            'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                            'position': snippet.get('position', 0),
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
                
                # Get video details for duration and views
                if video_ids:
                    details = await self._get_video_details(video_ids)
                    for video in videos[-len(video_ids):]:
                        detail = details.get(video['id'], {})
                        video['duration'] = format_duration(detail.get('duration', ''))
                        video['duration_raw'] = detail.get('duration', '')
                        video['views'] = int(detail.get('statistics', {}).get('viewCount', 0))
                        video['views_formatted'] = format_views(video['views'])
                        video['is_short'] = self._is_short_video(detail.get('duration', ''))
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except Exception as e:
                print(f"Error fetching playlist: {e}")
                break
        
        return videos
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get information for a single video"""
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': video_id,
            'key': self.api_key
        }
        
        try:
            url = f"{self.base_url}/videos"
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = data.get('items', [])
            if not items:
                return None
            
            item = items[0]
            snippet = item['snippet']
            details = item.get('contentDetails', {})
            stats = item.get('statistics', {})
            
            return {
                'id': video_id,
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'thumbnail': snippet['thumbnails'].get('medium', {}).get('url', ''),
                'description': snippet['description'],
                'published_at': snippet['publishedAt'],
                'duration': format_duration(details.get('duration', '')),
                'duration_raw': details.get('duration', ''),
                'views': int(stats.get('viewCount', 0)),
                'views_formatted': format_views(int(stats.get('viewCount', 0))),
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'is_short': self._is_short_video(details.get('duration', ''))
            }
            
        except Exception as e:
            print(f"Error fetching video info: {e}")
            return None
