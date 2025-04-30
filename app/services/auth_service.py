from datetime import datetime, timedelta
import jwt
import os
import requests
from typing import Dict, Any
from fastapi import HTTPException
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
import base64
import math

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.auth0_domain = os.getenv("AUTH0_DOMAIN", "dev-yvvbyrf4gu0fxc1j.us.auth0.com")
        self.audience = os.getenv("AUTH0_AUDIENCE", f"https://{self.auth0_domain}/api/v2/")
        self.issuer = f"https://{self.auth0_domain}/"
        self.jwks_url = f"https://{self.auth0_domain}/.well-known/jwks.json"
        logger.info(f"Auth0 Configuration: domain={self.auth0_domain}, audience={self.audience}, issuer={self.issuer}")

    def _get_rsa_key(self, jwk: Dict[str, Any]) -> str:
        """Convert JWK to RSA key format"""
        exponent = base64.urlsafe_b64decode(jwk['e'] + '==')
        modulus = base64.urlsafe_b64decode(jwk['n'] + '==')
        
        # Create RSA public key
        public_numbers = rsa.RSAPublicNumbers(
            e=int.from_bytes(exponent, byteorder='big'),
            n=int.from_bytes(modulus, byteorder='big')
        )
        
        public_key = public_numbers.public_key(default_backend())
        
        return public_key

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a JWT token issued by Auth0.
        
        Args:
            token (str): The JWT token to verify
            
        Returns:
            Dict[str, Any]: The decoded token payload if valid
            
        Raises:
            HTTPException: If token verification fails
        """
        try:
            logger.info("Fetching JWKS from Auth0")
            # Get the JWKS (JSON Web Key Set)
            jwks = requests.get(self.jwks_url).json()
            
            # Get the unverified header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            logger.info(f"Token header: {unverified_header}")
            
            # Find the key in the JWKS
            rsa_key = None
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = self._get_rsa_key(key)
                    logger.info(f"Found matching key with kid: {key['kid']}")
                    break
            
            if not rsa_key:
                logger.error(f"No matching key found for kid: {unverified_header['kid']}")
                raise HTTPException(
                    status_code=401,
                    detail="Unable to find appropriate key"
                )

            # Verify the token
            logger.info(f"Verifying token with audience={self.audience}, issuer={self.issuer}")
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=self.audience,
                    issuer=self.issuer
                )
            except jwt.exceptions.InvalidAlgorithmError:
                logger.warning("RS256 algorithm failed, trying HS256")
                # If RS256 fails, try HS256 with the secret key
                secret_key = os.getenv("JWT_SECRET_KEY")
                if not secret_key:
                    raise HTTPException(
                        status_code=401,
                        detail="JWT_SECRET_KEY environment variable is not set"
                    )
                payload = jwt.decode(
                    token,
                    secret_key,
                    algorithms=["HS256"],
                    audience=self.audience,
                    issuer=self.issuer
                )
            
            logger.info(f"Token verified successfully: {payload}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        except jwt.exceptions.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail=f"Token verification failed: {str(e)}"
            ) 