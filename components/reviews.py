import requests
import streamlit as st

GOOGLE_API_KEY = ""  # replace with your key

def get_place_id(building_name):
    search_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": building_name,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(search_url, params=params)
    result = response.json()

    if result.get("candidates"):
        return result["candidates"][0]["place_id"]
    else:
        return None

def get_reviews(place_id):
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,rating,reviews",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(details_url, params=params)
    result = response.json()

    if result.get("result", {}).get("reviews"):
        return result["result"]["reviews"]
    else:
        return []

def show_google_reviews():
    st.header("⭐ Building Google Reviews")

    building_name = st.text_input("Enter Building Name:")

    if building_name:
        st.write(f"Searching for **{building_name}**...")

        place_id = get_place_id(building_name)

        if place_id:
            reviews = get_reviews(place_id)

            if reviews:
                st.success(f"Found {len(reviews)} reviews!")

                # Split reviews into categories
                good_reviews = [r for r in reviews if r.get("rating", 0) >= 4]
                neutral_reviews = [r for r in reviews if r.get("rating", 0) == 3]
                bad_reviews = [r for r in reviews if r.get("rating", 0) <= 2]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("😊 Good Reviews")
                    for review in good_reviews:
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #d4edda;
                                padding: 0.8rem;
                                border-radius: 0.5rem;
                                margin-bottom: 1rem;
                                ">
                                <strong>{review.get('author_name', 'Anonymous')}</strong><br>
                                ⭐ {review.get('rating', 0)}/5
                                <p>{review.get('text', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                with col2:
                    st.subheader("😐 Neutral Reviews")
                    for review in neutral_reviews:
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #fefefe;
                                padding: 0.8rem;
                                border-radius: 0.5rem;
                                margin-bottom: 1rem;
                                ">
                                <strong>{review.get('author_name', 'Anonymous')}</strong><br>
                                ⭐ {review.get('rating', 0)}/5
                                <p>{review.get('text', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                with col3:
                    st.subheader("😡 Bad Reviews")
                    for review in bad_reviews:
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #f8d7da;
                                padding: 0.8rem;
                                border-radius: 0.5rem;
                                margin-bottom: 1rem;
                                ">
                                <strong>{review.get('author_name', 'Anonymous')}</strong><br>
                                ⭐ {review.get('rating', 0)}/5
                                <p>{review.get('text', '')}</p>
                            </div>
                            """, unsafe_allow_html=True)

            else:
                st.warning("No reviews found for this building.")
        else:
            st.error("Could not find the building.")

# Call the function to run the app
show_google_reviews()
