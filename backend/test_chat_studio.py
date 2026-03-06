import requests

BASE_URL = "http://localhost:8000/api"


def main() -> None:
    with open("../test_financial_data.csv", "rb") as f:
        upload_res = requests.post(f"{BASE_URL}/upload", files={"file": f})
    print("upload", upload_res.status_code)
    upload_res.raise_for_status()

    file_id = upload_res.json()["file_id"]

    chat_res = requests.post(
        f"{BASE_URL}/chat",
        json={
            "file_id": file_id,
            "question": "What are top 3 spend categories and why do they matter?",
            "departments": ["engineering", "executive"],
        },
    )
    print("chat", chat_res.status_code)
    if chat_res.ok:
        print("chat keys", list(chat_res.json().keys()))
    else:
        print(chat_res.text[:200])

    studio_res = requests.post(
        f"{BASE_URL}/studio",
        json={
            "file_id": file_id,
            "asset_type": "executive_brief",
            "department": "executive",
            "custom_prompt": "Keep this very concise and board-ready.",
        },
    )
    print("studio", studio_res.status_code)
    if studio_res.ok:
        data = studio_res.json()
        print("studio title", data.get("title"))
        preview = (data.get("content") or "")[:140].replace("\n", " ")
        print("studio preview", preview)
    else:
        print(studio_res.text[:200])


if __name__ == "__main__":
    main()
