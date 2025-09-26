from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/itinerary", tags=["itinerary"])

# Static mock itinerary based on user's specification
MOCK_MUMBAI_ITINERARY: List[Dict[str, Any]] = [
  {
    "day": 1,
    "date": "Thu, May 1",
    "title": "Kochi to Mumbai & Hotel Check-in",
    "stops": [
      {
        "id": 1,
        "title": "Cochin International Airport (COK)",
        "time": "10:00 AM - 11:30 AM (Check-in & Boarding)",
        "image": "https://upload.wikimedia.org/wikipedia/commons/c/c2/CIAL_T.jpg",
        "action": "Details",
        "actionType": "secondary",
        "distance": "34 km"
      },
      {
        "id": 2,
        "title": "Flight – Akasa Air QP 1519",
        "time": "11:50 AM - 1:55 PM (Non-stop, 2h 05m)",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWu6o7HTTei-IOWJAf1mrCVWyZ-UzDatnFSg&s",
        "action": "Book",
        "actionType": "primary",
        "distance": "1,511 km"
      },
      {
        "id": 3,
        "title": "Hotel Bawa Continental, Juhu",
        "time": "Check-in 3:00 PM (2 nights)",
        "image": "https://gos3.ibcdn.com/0ba5c43ec4d411e8a5d1023b42bcea16.jfif",
        "action": "Book",
        "actionType": "primary",
        "distance": "8.85 km from Airport"
      },
      {
        "id": 4,
        "title": "Evening at Juhu Beach",
        "time": "5:30 PM - 8:00 PM",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRqRedc1aZ6SPe1FUuwS0R7PS6S5rf9lgcOjg&s",
        "action": "Explore",
        "actionType": "secondary",
        "distance": "0.48 km walk"
      }
    ]
  },
  {
    "day": 2,
    "date": "Fri, May 2",
    "title": "South Mumbai Sightseeing",
    "stops": [
      {
        "id": 1,
        "title": "Gateway of India",
        "time": "9:00 AM - 10:00 AM",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Historical_Gateway_Of_India.jpg/1024px-Historical_Gateway_Of_India.jpg",
        "action": "Details",
        "actionType": "secondary",
        "distance": "27 km"
      },
      {
        "id": 2,
        "title": "Elephanta Caves (via Ferry)",
        "time": "10:30 AM - 2:00 PM",
        "image": "https://assets.cntraveller.in/photos/60ba04ee1fa22668f02596f6/16:9/w_1024%2Cc_limit/elephantalead.jpg",
        "action": "Book",
        "actionType": "primary",
        "distance": "9.65 km by ferry"
      },
      {
        "id": 3,
        "title": "Colaba Causeway (Shopping & Lunch)",
        "time": "2:30 PM - 4:30 PM",
        "image": "https://boundlessexplorism.com/wp-content/uploads/2023/12/blog-photos.webp",
        "action": "Explore",
        "actionType": "secondary",
        "distance": "1.61 km"
      },
      {
        "id": 4,
        "title": "Marine Drive & Chowpatty Beach",
        "time": "5:00 PM - 8:00 PM",
        "image": "https://afar.brightspotcdn.com/dims4/default/5b418b6/2147483647/strip/false/crop/1600x800+0+0/resize/1486x743!/quality/90/?url=https%3A%2F%2Fk3-prod-afar-media.s3.us-west-2.amazonaws.com%2Fbrightspot%2Fb2%2F3f%2Ff0d91e08ce68a99bfc194c256926%2Foriginal-8f0838e24dde673f351f3f85a97a8d7a.jpg",
        "action": "Details",
        "actionType": "secondary",
        "distance": "4 km"
      }
    ]
  },
  {
    "day": 3,
    "date": "Sat, May 3",
    "title": "Bandra & Flight Back",
    "stops": [
      {
        "id": 1,
        "title": "Bandra Fort & Bandstand Promenade",
        "time": "9:00 AM - 11:00 AM",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/Mumbai_Bandstand_Promenade.jpg/1200px-Mumbai_Bandstand_Promenade.jpg",
        "action": "Explore",
        "actionType": "secondary",
        "distance": "9.65 km"
      },
      {
        "id": 2,
        "title": "Hill Road & Linking Road (Shopping)",
        "time": "11:30 AM - 2:00 PM",
        "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/08/b7/71/af/photo0jpg.jpg?w=900&h=500&s=1",
        "action": "Details",
        "actionType": "secondary",
        "distance": "1.61 km"
      },
      {
        "id": 3,
        "title": "Hotel Checkout",
        "time": "3:00 PM",
        "image": "https://gos3.ibcdn.com/0ba5c43ec4d411e8a5d1023b42bcea16.jfif",
        "action": "Details",
        "actionType": "secondary",
        "distance": "-"
      },
      {
        "id": 4,
        "title": "Flight – SpiceJet SG 132",
        "time": "5:20 PM - 7:25 PM (Non-stop, 2h 05m)",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQgq3zkYqfQcf-fD3O97HQBid1kWRF9vaa8gA&s",
        "action": "Book",
        "actionType": "primary",
        "distance": "1,511 km"
      }
    ]
  }
]


@router.get("/mock")
def get_mock_itinerary() -> Dict[str, Any]:
    """Return the static Mumbai itinerary mock for UI consumption."""
    return {"itinerary": MOCK_MUMBAI_ITINERARY}
