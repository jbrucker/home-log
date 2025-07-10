# Login and get an access token:
#{
#  "access_token": #"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NTIxNTA2NjR9.rRE4xEKD8wMf2i7jifhZod72pN53WSzMnKVtRAAId0w"
#  "token_type": "bearer"
#}

# Paste the token:
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NTIxNTA2NjR9.rRE4xEKD8wMf2i7jifhZod72pN53WSzMnKVtRAAId0w"

# Curl request
curl -v -X DELETE http://localhost:8000/users/6 \
  -H "Authorization: Bearer ${TOKEN}"

