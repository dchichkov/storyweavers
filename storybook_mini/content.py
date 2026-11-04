"""Two original, fixed narrative streams; no condition-specific prose here."""
from .model import Entity as E, Fact as F, Story


LANTERN = Story("lantern", "A Light at the Landing", (
    E("mara", "girl", "Mara", "she", {"location": "cottage"}, {"Fear": 0.1}),
    E("oren", "ferryman", "Oren", "he", {"location": "landing"}),
    E("cottage", "cottage"), E("landing", "river landing"),
    E("lantern", "brass lantern", state={"lit": False, "owner": "mara"}),
    E("hook", "iron hook"), E("wind", "wind"),
), (
    F("l01", "home", "live", "mara", target="cottage", cue="Once upon a time"),
    F("l02", "home", "have", "mara", "lantern"),
    F("l03", "home", "need", "oren", "lantern", target="landing"),
    F("l04", "home", "light", "mara", "lantern", requires=(("lantern", "lit", False),),
      effects=(("lantern", "lit", True),)),
    F("l05", "home", "carry", "mara", "lantern", target="landing",
      requires=(("lantern", "lit", True), ("lantern", "owner", "mara")),
      effects=(("mara", "location", "landing"), ("lantern", "location", "landing"))),
    F("l06", "wind", "extinguish", "wind", "lantern", cue="On the riverbank",
      requires=(("lantern", "lit", True),), effects=(("lantern", "lit", False),),
      meme_deltas=(("mara", "Fear", 0.6),)),
    F("l07", "wind", "feel", "mara", value="Fear", cause="l06"),
    F("l08", "wind", "say", "oren", value="Cup your hands around the flame."),
    F("l09", "wind", "shield", "mara", "lantern", effects=(("lantern", "shielded", True),)),
    F("l10", "wind", "light", "mara", "lantern",
      requires=(("lantern", "lit", False), ("lantern", "shielded", True)),
      effects=(("lantern", "lit", True),), meme_deltas=(("mara", "Fear", -0.6),)),
    F("l11", "landing", "hang", "mara", "lantern", target="hook", cue="At the landing",
      requires=(("lantern", "lit", True), ("mara", "location", "landing")),
      effects=(("lantern", "location", "hook"),)),
    F("l12", "landing", "thank", "oren", "mara", cause="l11"),
    F("l13", "landing", "feel", "mara", value="Fear", cause="l10"),
    F("l14", "landing", "shine", "lantern", target="landing", cue="As night fell",
      requires=(("lantern", "lit", True), ("lantern", "location", "hook"))),
))

KITE = Story("kite", "The Kite with a Blue Patch", (
    E("tomas", "boy", "Tomas", "he", {"location": "hill"}, {"Sadness": 0.0}),
    E("ada", "girl", "Ada", "she", {"location": "hill"}),
    E("hill", "grassy hill"), E("kite", "red kite", state={"condition": "whole", "owner": "tomas"}),
    E("branch", "low branch"), E("patch", "blue patch", state={"owner": "ada"}),
    E("sky", "evening sky"),
), (
    F("k01", "hill", "have", "tomas", "kite", cue="One windy afternoon"),
    F("k02", "hill", "go", "tomas", target="hill", effects=(("tomas", "location", "hill"),)),
    F("k03", "hill", "meet", "tomas", "ada"),
    F("k04", "hill", "launch", "tomas", "kite",
      requires=(("kite", "condition", "whole"),), effects=(("kite", "airborne", True),)),
    F("k05", "snag", "snag", "kite", target="branch", cue="A moment later",
      requires=(("kite", "airborne", True),),
      effects=(("kite", "condition", "torn"), ("kite", "airborne", False)),
      meme_deltas=(("tomas", "Sadness", 0.8),)),
    F("k06", "snag", "retrieve", "tomas", "kite", target="branch",
      effects=(("kite", "location", "tomas"),)),
    F("k07", "snag", "be", "kite", value="torn"),
    F("k08", "snag", "feel", "tomas", value="Sadness", cause="k07"),
    F("k09", "snag", "say", "ada", value="We can mend it together."),
    F("k10", "repair", "give", "ada", "patch", target="tomas",
      requires=(("patch", "owner", "ada"),), effects=(("patch", "owner", "tomas"),)),
    F("k11", "repair", "mend", "tomas", "kite", target="patch",
      requires=(("kite", "condition", "torn"), ("patch", "owner", "tomas")),
      effects=(("kite", "condition", "mended"), ("patch", "location", "kite")),
      meme_deltas=(("tomas", "Sadness", -0.7),)),
    F("k12", "repair", "thank", "tomas", "ada", cause="k10"),
    F("k13", "flight", "launch", "tomas", "kite", cue="Before sunset",
      requires=(("kite", "condition", "mended"),), effects=(("kite", "airborne", True),)),
    F("k14", "flight", "feel", "tomas", value="Sadness", cause="k11"),
    F("k15", "flight", "glow", "patch", target="sky",
      requires=(("kite", "airborne", True), ("kite", "condition", "mended"),
                ("patch", "location", "kite"))),
))

STORIES = {s.id: s for s in (LANTERN, KITE)}
MINI_IDS = tuple(STORIES)
from .extended_content import EXTENDED_STORIES
STORIES.update(EXTENDED_STORIES)
EXTENDED_IDS = tuple(EXTENDED_STORIES)
SUITES = {"mini": MINI_IDS, "extended": EXTENDED_IDS, "all": tuple(STORIES)}
