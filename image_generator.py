import requests

STABLE_DIFFUSION_API_URL = "https://api.stablediffusionapi.com/v3/text-to-image"
STABLE_DIFFUSION_API_KEY = "your_api_key"

def generate_image_from_text(text):
    headers = {
        "Authorization": f"Bearer {STABLE_DIFFUSION_API_KEY}"
    }
    payload = {
        "text": text,
        "width": 512,
        "height": 512
    }
    response = requests.post(STABLE_DIFFUSION_API_URL, json=payload, headers=headers)
    image_url = response.json().get('image_url')
    image = requests.get(image_url).content
    
    with open('output/generated_image.png', 'wb') as f:
        f.write(image)
    print("Image generated and saved to 'output/generated_image.png'")

if __name__ == "__main__":
    text = "A futuristic city at sunset"
    generate_image_from_text(text)
