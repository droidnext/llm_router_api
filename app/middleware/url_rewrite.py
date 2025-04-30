from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import re
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

logger = logging.getLogger(__name__)

class URLRewriteMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get the original URL
        original_url = str(request.url)
        
        # Check if URL contains query parameters in the middle
        if '?' in original_url and not original_url.endswith('?'):
            # Split the URL into parts
            parsed_url = urlparse(original_url)
            path_parts = parsed_url.path.split('/')
            
            # Find the position of the query parameter
            query_pos = None
            for i, part in enumerate(path_parts):
                if '?' in part:
                    query_pos = i
                    break
            
            if query_pos is not None:
                # Extract the query parameters
                query_part = path_parts[query_pos]
                base_path, query_string = query_part.split('?', 1)
                
                # Log the found query parameters
                logger.info(f"Found query parameters in URL: {query_string}")
                
                # Reconstruct the path without query parameters
                new_path_parts = path_parts[:query_pos] + [base_path] + path_parts[query_pos + 1:]
                new_path = '/'.join(new_path_parts)
                
                # Combine existing query parameters with the ones from the path
                existing_query = parse_qs(parsed_url.query)
                path_query = parse_qs(query_string)
                combined_query = {**existing_query, **path_query}
                
                # Log the combined query parameters
                logger.info(f"Combined query parameters: {combined_query}")
                
                # Create new URL with query parameters at the end
                new_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    new_path,
                    parsed_url.params,
                    urlencode(combined_query, doseq=True),
                    parsed_url.fragment
                ))
                
                # Log the URL rewrite with details
                logger.warning(
                    f"URL Rewrite:\n"
                    f"Original URL: {original_url}\n"
                    f"New URL: {new_url}\n"
                    f"Path before: {parsed_url.path}\n"
                    f"Path after: {new_path}\n"
                    f"Query parameters moved: {list(combined_query.keys())}"
                )
                
                # Create a new request with the rewritten URL
                request.scope["path"] = new_path
                request.scope["query_string"] = urlencode(combined_query, doseq=True).encode()
                request.scope["raw_path"] = new_path.encode()
        
        # Continue with the request
        response = await call_next(request)
        return response 