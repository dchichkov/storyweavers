"""Two fixed paths through one small borrowed-resource narrative.

The content author owns goals, quoted words, effects and rhetorical relations.
No prose condition has access to the route decision; all consume the same trace.
"""
from .model import Entity as E, Fact, Proposition as P, Story


def borrowed_lamp(fuel=3):
    """A bounded content author: sufficient oil permits supper, scarce oil does not."""
    if fuel not in (1, 3):
        raise ValueError("This authored content family supports one or three oil measures")
    successful = fuel == 3
    story_id = "lamp_supper" if successful else "lamp_return"
    entities = (
        E("nell", "girl", "Nell", "she", {"location": "cottage"}, {"Sadness": 0.0}),
        E("ada", "girl", "Ada", "she", {"location": "cottage"}),
        E("iris", "neighbor", "Iris", "she", {"location": "workshop", "knows_supper": False}),
        E("cottage", "small cottage", short_noun="cottage"),
        E("kitchen", "windowless kitchen", short_noun="kitchen"),
        E("workshop", "stone workshop", short_noun="workshop"),
        E("gate", "garden gate", short_noun="gate"),
        E("table", "wooden table", short_noun="table"),
        E("shelf", "stone shelf", short_noun="shelf"),
        E("oven", "brick oven", short_noun="oven", state={"condition": "hot"}),
        E("loaf", "plaited loaf", short_noun="loaf", state={"condition": "unbaked", "baked": False}),
        E("card", "folded invitation", short_noun="invitation", state={"owner": "ada", "condition": "ready"}),
        E("basket", "wicker basket", short_noun="basket"),
        E("cloth", "white cloth", short_noun="cloth"),
        E("lamp", "brass lamp", short_noun="lamp", state={
            "owner": "iris", "custodian": "iris", "location": "workshop", "lit": False,
            "condition": "unlit", "fuel": fuel, "return_due": False}),
        E("reservoir", "glass reservoir", short_noun="reservoir", state={
            "condition": "half full" if successful else "almost empty"}),
        E("wheel", "brass wheel", short_noun="wheel", state={"condition": "stiff"}),
        E("steps", "cellar steps", "", "they", number="plural", definite=True, state={"owner": "iris"}),
        E("door", "kitchen door", short_noun="door", state={"closed": True}),
    )
    facts = []

    def add(scene, predicate, subject, object="", target="", **kw):
        fid = f"b{len(facts)+1:02d}"
        facts.append(Fact(fid, scene, predicate, subject, object, target, **kw))
        return fid

    add("premise", "live", "nell", target="cottage", cue="Once upon a time")
    add("premise", "want", "nell", goal=P("bake", "nell", "loaf"))
    add("premise", "have", "ada", "card")
    add("premise", "say", "nell", listener="ada",
        value="Iris is leaving tomorrow; a warm loaf might persuade her to stay for supper.")
    add("premise", "take", "nell", "basket")
    add("premise", "take", "nell", "cloth")
    add("premise", "say", "ada", listener="nell",
        value="A basket is a hopeful start for a loaf we have not baked.")
    add("premise", "go", "nell", target="workshop", companion="ada",
        effects=(("nell", "location", "workshop"), ("ada", "location", "workshop")))

    add("loan", "stand", "iris", target="gate")
    add("loan", "have", "iris", "lamp")
    add("loan", "say", "nell", listener="iris",
        value="May we borrow your lamp until six; our oven room has no light?")
    add("loan", "say", "iris", listener="nell", speech=P("need_for", "iris", "lamp", "steps"))
    add("loan", "say", "iris", listener="nell",
        value="Leave one measure of oil for the steps; they are steep enough in daylight.")
    add("loan", "lend", "iris", "lamp", "nell",
        requires=(("lamp", "custodian", "iris"),),
        effects=(("lamp", "custodian", "nell"), ("lamp", "return_due", True)))
    add("loan", "say", "nell", listener="iris", speech=P("return", "nell", "lamp", "iris", tense="future"))
    add("loan", "carry", "nell", "lamp", "kitchen", companion="ada",
        requires=(("lamp", "custodian", "nell"),),
        effects=(("lamp", "location", "kitchen"), ("nell", "location", "kitchen"),
                 ("ada", "location", "kitchen")))

    add("inspection", "put", "ada", "cloth", "table", effects=(("cloth", "location", "table"),))
    add("inspection", "check", "nell", "reservoir")
    add("inspection", "be", "reservoir", value="half full" if successful else "almost empty")
    add("inspection", "check", "nell", "wheel")
    add("inspection", "be", "wheel", value="stiff")
    add("inspection", "say", "ada", listener="nell",
        value="That little wheel has the manners of a locked front door.")
    add("inspection", "turn", "nell", "wheel", requires=(("wheel", "condition", "stiff"),),
        effects=(("wheel", "condition", "free"),))

    if successful:
        add("baking", "light", "nell", "lamp",
            requires=(("wheel", "condition", "free"), ("lamp", "lit", False), ("lamp", "fuel", 3)),
            effects=(("lamp", "lit", True), ("lamp", "condition", "alight")))
        add("baking", "put", "nell", "lamp", "shelf", effects=(("lamp", "location", "shelf"),))
        add("baking", "put_in", "nell", "loaf", "oven", effects=(("loaf", "location", "oven"),))
        add("baking", "bake", "nell", "loaf",
            requires=(("lamp", "lit", True), ("lamp", "fuel", 3), ("loaf", "condition", "unbaked")),
            effects=(("loaf", "condition", "half baked"), ("lamp", "fuel", 2)))
        add("baking", "say", "ada", listener="nell",
            value="It smells like supper already; perhaps we should invite the smell first.")
        add("visit", "arrive", "iris", target="kitchen", cue="Before the second baking interval",
            effects=(("iris", "location", "kitchen"),))
        add("visit", "open", "ada", "door", effects=(("door", "closed", False),))
        add("visit", "say", "iris", listener="nell", speech=P("need_for", "iris", "lamp", "steps"))
        add("visit", "say", "nell", listener="iris",
            value="The loaf is for your leaving supper; will you give it ten more minutes?",
            effects=(("iris", "knows_supper", True),))
        add("visit", "say", "iris", listener="nell",
            value="Ten minutes, then; I can finish packing the counter before going downstairs.",
            requires=(("iris", "knows_supper", True),), effects=(("lamp", "extension", True),))
        add("finish", "check", "nell", "reservoir")
        add("finish", "bake", "nell", "loaf",
            requires=(("lamp", "extension", True), ("lamp", "fuel", 2), ("loaf", "condition", "half baked")),
            effects=(("lamp", "fuel", 1), ("loaf", "condition", "warm"), ("loaf", "baked", True)))
        add("finish", "put", "nell", "loaf", "table", effects=(("loaf", "location", "table"),))
        add("finish", "be", "loaf", value="warm")
        add("finish", "smell", "iris", "loaf")
        add("finish", "say", "iris", listener="ada",
            value="Now I understand the basket; I thought you were borrowing my whole kitchen.")
    else:
        want = add("decision", "want", "nell", goal=P("bake", "nell", "loaf"))
        add("decision", "light", "nell", "lamp", negative=True, contrast=want)
        add("decision", "say", "ada", listener="nell",
            value="If the lamp stays cold, is this still a surprise supper?")
        add("decision", "say", "nell", listener="ada",
            value="The last measure belongs to her steps; a loaf cannot make them less steep.")
        shut = add("decision", "close", "nell", "oven", effects=(("oven", "closed", True),),
                   meme_deltas=(("nell", "Sadness", 0.7),))
        add("decision", "feel", "nell", value="Sadness", cause=shut)
        add("decision", "say", "ada", listener="nell",
            value="Then let us ask about breakfast instead; there is room on the invitation.")
        add("decision", "carry", "nell", "lamp", "workshop", companion="ada",
            requires=(("lamp", "lit", False), ("lamp", "fuel", 1)),
            effects=(("lamp", "location", "workshop"), ("nell", "location", "workshop"),
                     ("ada", "location", "workshop")))
        add("decision", "say", "nell", listener="iris",
            value="We hoped to give you supper; may we bring a loaf tomorrow, if you are still here?",
            effects=(("iris", "knows_supper", True),))
        add("decision", "say", "iris", listener="nell",
            value="Ask me in the morning; the van has not told me its plans either.")

    if successful:
        add("return", "extinguish", "nell", "lamp", requires=(("lamp", "lit", True),),
            effects=(("lamp", "lit", False), ("lamp", "condition", "unlit")))
    add("return", "return", "nell", "lamp", "iris",
        requires=(("lamp", "custodian", "nell"), ("lamp", "return_due", True), ("lamp", "fuel", 1)),
        effects=(("lamp", "custodian", "iris"), ("lamp", "return_due", False),
                 ("lamp", "location", "iris")))
    add("return", "check", "iris", "lamp")
    add("return", "be", "lamp", value="unlit")
    gift = add("return", "give", "ada", "card", "iris",
               requires=(("card", "owner", "ada"),), effects=(("card", "owner", "iris"),))
    add("return", "smile", "iris", cause=gift)
    add("return", "say", "iris", listener="ada", speech=P("keep", "iris", "card", tense="future"))
    add("image", "light", "iris", "lamp", cue="At six",
        requires=(("lamp", "fuel", 1), ("lamp", "custodian", "iris"), ("lamp", "lit", False)),
        effects=(("lamp", "lit", True), ("lamp", "condition", "alight")))
    add("image", "go", "iris", target="steps", effects=(("iris", "location", "steps"),))
    add("image", "be", "loaf", value="warm" if successful else "unbaked")
    add("image", "shine", "lamp", target="steps",
        requires=(("lamp", "lit", True), ("lamp", "custodian", "iris"),
                  ("iris", "location", "steps"), ("lamp", "return_due", False)))
    return Story(story_id, "Supper Before Six" if successful else "The Measure Left for the Steps", entities, tuple(facts))


EXTENDED_STORIES = {s.id: s for s in (borrowed_lamp(3), borrowed_lamp(1))}
