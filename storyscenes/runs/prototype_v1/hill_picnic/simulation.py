import random

from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell


def build(seed: int) -> WorldSpec:
    rng = random.Random(seed)
    arrangement = rng.randrange(3)

    if arrangement == 0:
        path_condition = "gentle"
        wind = "calm"
        noor_need = "slow_steps"
        noor_preference = "view"
        basket_capacity = 3
    elif arrangement == 1:
        path_condition = "muddy"
        wind = "gusty"
        noor_need = "unsteady_footing"
        noor_preference = "shelter"
        basket_capacity = 2
    else:
        path_condition = "muddy"
        wind = "calm"
        noor_need = "unsteady_footing"
        noor_preference = "view"
        basket_capacity = 2

    entities = {
        "ada": {"name": "Ada", "kind": "child"},
        "ben": {"name": "Ben", "kind": "child"},
        "moss": {"name": "Moss", "kind": "donkey"},
        "noor": {"name": "Noor", "kind": "neighbor"},
        "hillfoot": {"name": "hill foot", "kind": "place"},
        "hilltop": {"name": "hilltop", "kind": "place"},
        "shelter": {"name": "small shelter", "kind": "place"},
        "path": {"name": "hill path", "kind": "path"},
        "weather": {"name": "weather", "kind": "weather"},
        "picnic": {"name": "picnic", "kind": "arrangement"},
        "basket": {"name": "pannier basket", "kind": "container"},
        "viewbag": {"name": "little view bag", "kind": "container"},
        "mainfood": {"name": "bread and fruit bundle", "kind": "food"},
        "viewfood": {"name": "two apple slices", "kind": "food"},
        "blanket": {"name": "picnic blanket", "kind": "prop"},
        "cloth": {"name": "windbreak cloth", "kind": "prop"},
        "water": {"name": "water pail", "kind": "prop"},
        "cart": {"name": "handcart", "kind": "vehicle"},
        "note": {"name": "hilltop note", "kind": "message"},
    }

    initial = {
        "ada.location": "hillfoot",
        "ada.memes.Curiosity": 2,
        "ada.memes.Care": 2,
        "ada.memes.Ambition": 2,
        "ada.knows.path.condition": None,
        "ada.knows.noor.need": None,
        "ada.knows.noor.preference": None,
        "ben.location": "hillfoot",
        "ben.memes.Care": 2,
        "ben.memes.Practicality": 2,
        "moss.location": "hillfoot",
        "moss.memes.Care": 1,
        "moss.memes.Comfort": 2,
        "moss.knows.path.condition": None,
        "moss.ready": False,
        "noor.location": "hillfoot",
        "noor.need": noor_need,
        "noor.preference": noor_preference,
        "noor.included": False,
        "path.condition": path_condition,
        "weather.wind": wind,
        "shelter.location": "hillfoot",
        "picnic.place": None,
        "picnic.arranged": False,
        "picnic.served": False,
        "basket.owner": "shelter",
        "basket.location": "hillfoot",
        "basket.load": 0,
        "basket.capacity": basket_capacity,
        "viewbag.owner": "shelter",
        "viewbag.location": "hillfoot",
        "viewbag.load": 0,
        "mainfood.owner": "shelter",
        "mainfood.location": "shelter",
        "viewfood.owner": "shelter",
        "viewfood.location": "shelter",
        "blanket.owner": "shelter",
        "blanket.location": "shelter",
        "cloth.owner": "shelter",
        "cloth.location": "shelter",
        "cloth.erected": False,
        "water.owner": "shelter",
        "water.location": "hillfoot",
        "cart.location": "hillfoot",
        "cart.wheel": "fixed",
        "note.location": "shelter",
    }

    scenes = (
        observe(
            "inspect_path",
            "ada",
            "path.condition",
            requires=(
                C("ada.location", "eq", "hillfoot"),
                C("ada.memes.Curiosity", "ge", 1),
            ),
            summary="Ada examined the hill path with her muddy-finger test",
        ),
        Scene(
            "ask_noor",
            "care",
            ("ada", "noor"),
            (
                C("ada.location", "eq", "hillfoot"),
                C("noor.location", "eq", "hillfoot"),
                C("ada.knows.noor.need", "eq", None),
                C("ada.memes.Care", "ge", 1),
            ),
            (
                E("ada.knows.noor.need", noor_need),
                E("ada.knows.noor.preference", noor_preference),
            ),
            "Ada asked Noor what would make the picnic comfortable",
        ),
        tell(
            "tell_moss_path",
            "ada",
            "moss",
            "path.condition",
            requires=(
                C("ada.location", "eq", "hillfoot"),
                C("moss.location", "eq", "hillfoot"),
                C("ada.knows.noor.need", "ne", None),
            ),
            summary="Ada told Moss what the path and Noor both required",
        ),
        Scene(
            "pack_small_picnic",
            "cooperation",
            ("ada", "ben", "basket", "viewbag"),
            (
                C("ada.location", "eq", "hillfoot"),
                C("ben.location", "eq", "hillfoot"),
                C("basket.location", "eq", "hillfoot"),
                C("mainfood.location", "eq", "shelter"),
                C("viewfood.location", "eq", "shelter"),
                C("blanket.location", "eq", "shelter"),
                C("basket.capacity", "ge", 2),
                C("ada.knows.noor.preference", "ne", None),
                C("ben.memes.Care", "ge", 1),
            ),
            (
                E("basket.owner", "ada"),
                E("basket.load", 2),
                E("mainfood.owner", "ada"),
                E("mainfood.location", "basket"),
                E("viewbag.owner", "ben"),
                E("viewbag.load", 1),
                E("viewfood.owner", "ben"),
                E("viewfood.location", "viewbag"),
                E("blanket.owner", "ada"),
                E("blanket.location", "basket"),
            ),
            "Ada and Ben packed the substantial food separately from the tiny view snack",
        ),
        Scene(
            "invite_moss_rest",
            "care",
            ("ada", "moss", "water"),
            (
                C("ada.location", "eq", "hillfoot"),
                C("moss.location", "eq", "hillfoot"),
                C("water.location", "eq", "hillfoot"),
                C("moss.ready", "eq", False),
                C("ada.memes.Care", "ge", 1),
            ),
            (
                E("water.owner", "moss"),
                E("water.location", "moss"),
                E("moss.ready", True),
            ),
            "Ada offered Moss water and a quiet minute before asking for help",
        ),
        Scene(
            "roll_cart_to_shelter",
            "cooperation",
            ("ada", "ben", "cart", "basket"),
            (
                C("path.condition", "eq", "muddy"),
                C("noor.need", "eq", "unsteady_footing"),
                C("cart.location", "eq", "hillfoot"),
                C("cart.wheel", "eq", "fixed"),
                C("basket.location", "eq", "hillfoot"),
                C("basket.load", "eq", 2),
                C("moss.knows.path.condition", "eq", "muddy"),
            ),
            (
                E("cart.location", "shelter"),
                E("basket.location", "shelter"),
                E("ada.location", "shelter"),
                E("ben.location", "shelter"),
                E("moss.location", "shelter"),
            ),
            "Ada and Ben rolled the manageable basket to the shelter while Moss guided them",
        ),
        Scene(
            "carry_picnic_up",
            "ambition",
            ("ada", "ben", "moss", "noor", "basket", "viewbag"),
            (
                C("path.condition", "eq", "gentle"),
                C("weather.wind", "eq", "calm"),
                C("noor.need", "eq", "slow_steps"),
                C("ada.knows.noor.need", "eq", "slow_steps"),
                C("moss.knows.path.condition", "eq", "gentle"),
                C("moss.ready", "eq", True),
                C("basket.location", "eq", "hillfoot"),
                C("basket.load", "le", 3),
                C("viewbag.location", "eq", "hillfoot"),
            ),
            (
                E("ada.location", "hilltop"),
                E("ben.location", "hilltop"),
                E("moss.location", "hilltop"),
                E("noor.location", "hilltop"),
                E("basket.location", "hilltop"),
                E("viewbag.location", "hilltop"),
            ),
            "The group took the gentle path slowly, with Moss carrying only the safe load",
        ),
        Scene(
            "spread_hilltop_blanket",
            "cooperation",
            ("ada", "ben", "blanket"),
            (
                C("ada.location", "eq", "hilltop"),
                C("ben.location", "eq", "hilltop"),
                C("noor.location", "eq", "hilltop"),
                C("basket.location", "eq", "hilltop"),
                C("blanket.location", "eq", "basket"),
                C("picnic.arranged", "eq", False),
            ),
            (
                E("blanket.location", "hilltop"),
                E("picnic.place", "hilltop"),
                E("picnic.arranged", True),
            ),
            "Ada and Ben spread the blanket where Noor could sit and see the whole valley",
        ),
        Scene(
            "raise_windbreak",
            "care",
            ("ada", "ben", "noor", "cloth"),
            (
                C("weather.wind", "eq", "gusty"),
                C("noor.preference", "eq", "shelter"),
                C("cloth.location", "eq", "shelter"),
                C("cloth.erected", "eq", False),
                C("ada.location", "eq", "shelter"),
                C("ben.location", "eq", "shelter"),
            ),
            (
                E("cloth.owner", "ada"),
                E("cloth.erected", True),
            ),
            "Ada and Ben tied the windbreak beside the shelter for Noor",
        ),
        Scene(
            "arrange_shelter_picnic",
            "care",
            ("ada", "ben", "moss", "noor", "basket", "blanket"),
            (
                C("weather.wind", "eq", "gusty"),
                C("noor.preference", "eq", "shelter"),
                C("cloth.erected", "eq", True),
                C("basket.location", "eq", "shelter"),
                C("mainfood.location", "eq", "basket"),
                C("picnic.arranged", "eq", False),
            ),
            (
                E("noor.location", "shelter"),
                E("blanket.location", "shelter"),
                E("picnic.place", "shelter"),
                E("picnic.arranged", True),
            ),
            "The group made a sheltered picnic place at the hill foot",
        ),
        Scene(
            "carry_view_bag_up",
            "ambition",
            ("ada", "ben", "moss", "viewbag", "note"),
            (
                C("path.condition", "eq", "muddy"),
                C("weather.wind", "eq", "calm"),
                C("noor.preference", "eq", "view"),
                C("moss.ready", "eq", True),
                C("moss.knows.path.condition", "eq", "muddy"),
                C("ada.location", "eq", "shelter"),
                C("ben.location", "eq", "shelter"),
                C("moss.location", "eq", "shelter"),
                C("viewbag.location", "eq", "hillfoot"),
                C("viewbag.load", "eq", 1),
            ),
            (
                E("ada.location", "hilltop"),
                E("ben.location", "hilltop"),
                E("moss.location", "hilltop"),
                E("viewbag.location", "hilltop"),
                E("note.location", "hilltop"),
            ),
            "Ada, Ben, and Moss carried only the little view bag to the hilltop",
        ),
        Scene(
            "return_from_view",
            "cooperation",
            ("ada", "ben", "moss", "viewbag"),
            (
                C("ada.location", "eq", "hilltop"),
                C("ben.location", "eq", "hilltop"),
                C("moss.location", "eq", "hilltop"),
                C("viewbag.location", "eq", "hilltop"),
                C("note.location", "eq", "hilltop"),
                C("noor.location", "eq", "hillfoot"),
            ),
            (
                E("ada.location", "shelter"),
                E("ben.location", "shelter"),
                E("moss.location", "shelter"),
                E("viewbag.location", "shelter"),
            ),
            "They returned with a hilltop note instead of asking Noor to face the mud",
        ),
        Scene(
            "arrange_split_picnic",
            "cooperation",
            ("ada", "ben", "moss", "noor", "basket", "blanket"),
            (
                C("weather.wind", "eq", "calm"),
                C("noor.preference", "eq", "view"),
                C("path.condition", "eq", "muddy"),
                C("note.location", "eq", "hilltop"),
                C("basket.location", "eq", "shelter"),
                C("mainfood.location", "eq", "basket"),
                C("picnic.arranged", "eq", False),
            ),
            (
                E("noor.location", "shelter"),
                E("blanket.location", "shelter"),
                E("picnic.place", "shelter"),
                E("picnic.arranged", True),
            ),
            "The friends arranged the main picnic below, with the hilltop note between them",
        ),
        Scene(
            "serve_hilltop_picnic",
            "care",
            ("ada", "ben", "moss", "noor", "mainfood"),
            (
                C("picnic.place", "eq", "hilltop"),
                C("picnic.arranged", "eq", True),
                C("noor.location", "eq", "hilltop"),
                C("mainfood.location", "eq", "basket"),
                C("picnic.served", "eq", False),
            ),
            (
                E("picnic.served", True),
                E("noor.included", True),
            ),
            "Noor shared bread and fruit at the hilltop picnic while Moss rested nearby",
        ),
        Scene(
            "serve_shelter_picnic",
            "care",
            ("ada", "ben", "moss", "noor", "mainfood"),
            (
                C("picnic.place", "eq", "shelter"),
                C("weather.wind", "eq", "gusty"),
                C("cloth.erected", "eq", True),
                C("noor.location", "eq", "shelter"),
                C("mainfood.location", "eq", "basket"),
                C("picnic.served", "eq", False),
            ),
            (
                E("picnic.served", True),
                E("noor.included", True),
            ),
            "Noor shared the sheltered picnic while the windbreak fluttered outside",
        ),
        Scene(
            "serve_split_picnic",
            "care",
            ("ada", "ben", "moss", "noor", "mainfood", "note"),
            (
                C("picnic.place", "eq", "shelter"),
                C("weather.wind", "eq", "calm"),
                C("note.location", "eq", "hilltop"),
                C("noor.location", "eq", "shelter"),
                C("mainfood.location", "eq", "basket"),
                C("picnic.served", "eq", False),
            ),
            (
                E("picnic.served", True),
                E("noor.included", True),
            ),
            "Noor shared the hill-foot feast and read the little note from the hilltop",
        ),
    )

    rules = (
        Rule(
            "basket is never overloaded",
            (C("basket.load", "le", 3),),
        ),
        Rule(
            "a parked cart has a sound wheel",
            (C("cart.wheel", "eq", "fixed"),),
            (C("cart.location", "eq", "shelter"),),
        ),
        Rule(
            "an arranged picnic has food packed",
            (C("mainfood.location", "eq", "basket"),),
            (C("picnic.arranged", "eq", True),),
        ),
        Rule(
            "serving includes Noor at an arranged picnic",
            (
                C("picnic.arranged", "eq", True),
                C("noor.included", "eq", True),
            ),
            (C("picnic.served", "eq", True),),
        ),
    )

    return WorldSpec(
        "The Hill Picnic",
        entities,
        initial,
        scenes,
        (
            C("picnic.served", "eq", True),
            C("noor.included", "eq", True),
        ),
        rules=rules,
        labels={
            "path.condition": "condition of the hill path",
            "weather.wind": "strength of the wind",
            "picnic.place": "place of the completed picnic",
            "picnic.served": "whether food has been served",
            "noor.included": "whether Noor is included",
            "note.location": "location of the hilltop note",
        },
    )
