import os
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

def main():
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

    langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)

    prompt_v1_text = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
    prompt_v2_text = "Answer concisely.\nFeature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"

    print("--- Creating/Updating Prompt v1 (baseline, production) ---")
    p1 = langfuse.create_prompt(
        name="day13-chat",
        prompt=prompt_v1_text,
        type="text",
        labels=["baseline", "production"],
    )
    print(f"Prompt v1 created: version={p1.version}, labels={p1.labels}")

    print("\n--- Creating Prompt v2 (candidate) ---")
    p2 = langfuse.create_prompt(
        name="day13-chat",
        prompt=prompt_v2_text,
        type="text",
        labels=["candidate"],
    )
    print(f"Prompt v2 created: version={p2.version}, labels={p2.labels}")

    print("\n[SUCCESS] Ca hai version da duoc tao va gan nhan thanh cong tren Langfuse Cloud!")

if __name__ == "__main__":
    main()
