"""An authored fable-world. The director never receives a desired ending."""
from dataclasses import dataclass

from .engine import Memeplex, Microdrama, StoryError, World


TERMS = ("BlameWolf", "Obey", "Pride", "StatusThreat", "Curiosity", "DrainCraft",
         "BridgeCraft", "SharedWork", "ProtectBooks", "Question", "WantCheese", "WolfBuilder")
A = Memeplex.atom
SCAPEGOAT = A("BlameWolf", 3) + A("Obey", 2)
FOUNDATIONS = A("DrainCraft", 2) + A("Question", 1)
BRIDGES = A("BridgeCraft", 2) + A("Question", 1)


@dataclass(frozen=True)
class Parameters:
    access: str = "open"
    attention: int = 1
    work: str = "shared"
    mentor: bool = True
    witness: bool = False

    def validate(self):
        if self.access not in ("open", "locked") or self.work not in ("shared", "separate"):
            raise StoryError("Unknown access/work arrangement")
        if type(self.attention) is not int or self.attention not in (1, 2, 4):
            raise StoryError("Attention must be 1, 2, or 4")
        if type(self.mentor) is not bool or type(self.witness) is not bool:
            raise StoryError("Mentor and witness must be booleans")


def validate(s):
    if s["cottage.owner"] != "wolf":
        raise StoryError("Occupation does not change the cottage's ownership")
    for house, cause in (("straw", "wind"), ("wood", "mud"), ("brick", "bad_foundation")):
        if s[house + ".failed"] and s[house + ".cause"] != cause:
            raise StoryError("Propaganda must not overwrite physical causes")
    if s["cheese.portions"] < 0:
        raise StoryError("Cheese cannot be created by taking it")
    if s["palace.outcome"] == "library" and not (s["palace.public"] and s["books.accessible"]):
        raise StoryError("A library needs public access")
    if s["palace.public"] and s["palace.occupant"] != "valley":
        raise StoryError("Public use must have a physical occupant")
    if s["wolf.free"] and s["wolf.coerced"]:
        raise StoryError("Freedom and coercion cannot both hold")
    if s["wolf.home_restored"] and not (s["wolf.location"] == "creek" and s["cottage.occupant"] == "wolf"):
        raise StoryError("Restoration must be enacted")
    for child, prop in (("mira", "drain"), ("tansy", "bridge")):
        if s[child + ".skilled"] and not s[prop + ".works"]:
            raise StoryError("Skill needs a successful physical demonstration")
    if s["palace.outcome"] == "night_school" and s["foundations.location"] != "brick":
        raise StoryError("The night school must actually receive its book")


def build_world(params):
    params.validate()
    spec = {
        "valley": ("the valley", "group", "market"),
        "pigs": ("the Three Little Pigs", "group", "market"),
        "wolf": ("G. Wolf", "person", "creek"),
        "mira": ("Mira", "person", "market"),
        "tansy": ("Tansy", "person", "market"),
        "fox": ("Story Fox", "person", "edge"),
        "poster": ("the wolf poster", "paper", "market"),
        "newspaper": ("the pigs' newspaper", "paper", "market"),
        "foundations": ("the foundations book", "book", "depot"),
        "bridges": ("the bridge book", "book", "depot"),
        "books": ("the book collection", "collection", "depot"),
        "cottage": ("Wolf's cottage", "building", "creek"),
        "straw": ("the straw house", "building", "market"),
        "wood": ("the wooden house", "building", "market"),
        "brick": ("the brick house", "building", "brick"),
        "palace": ("the palace", "building", "hill"),
        "cheese": ("the lunch cheese", "food", "worksite"),
        "soup": ("Wolf's soup pot", "thing", "creek"),
        "drain": ("the model drain", "thing", "hill"),
        "bridge": ("the trial bridge", "thing", "hill"),
    }
    entities = {k: {"name": n, "kind": kind} for k, (n, kind, _) in spec.items()}
    state = {k + ".location": loc for k, (_, _, loc) in spec.items()}
    for k in entities:
        for term in TERMS:
            state[f"{k}.meme.{term}"] = 0.0
    state.update({
        "valley.phase": 0, "valley.ended": False, "valley.wind": 3, "valley.rain": 3,
        "valley.reporting": False, "valley.whispers": False, "valley.cottages_built": False,
        "valley.work_arrangement": params.work,
        "books.shelf_policy": params.access,
        "mira.attention_divisor": params.attention, "tansy.attention_divisor": params.attention,
        "mira.witness_position": params.witness, "wolf.teaching_available": params.mentor,
        "straw.capacity": 1, "straw.failed": False, "straw.cause": "",
        "wood.footing": 1, "wood.failed": False, "wood.cause": "",
        "brick.footing": 1, "brick.load": 3, "brick.failed": False, "brick.cause": "",
        "cottage.owner": "wolf", "cottage.occupant": "wolf",
        "wolf.coerced": False, "wolf.free": True, "wolf.home_restored": False,
        "pigs.claims_authorship": False, "pigs.commission": False, "pigs.claims_gift": False,
        "poster.printed": False, "newspaper.printed": False,
        "books.accessible": False, "books.delivered": False,
        "foundations.owner": "pigs", "bridges.owner": "pigs",
        "foundations.accessible": False, "bridges.accessible": False,
        "palace.owner": "pigs",
        "palace.occupant": "pigs", "palace.public": False, "palace.roof": False,
        "palace.outcome": "", "palace.coalition": False, "palace.dissenters": 0,
        "palace.books_removed": False, "palace.title": "Pig Palace",
        "cheese.portions": 3, "fox.took_cheese": False, "pigs.blame_cheese": False,
        "mira.saw_theft": False, "mira.read": False, "tansy.read": False,
        "mira.mentored": False, "tansy.mentored": False,
        "mira.skilled": False, "tansy.skilled": False,
        "mira.spoke": False, "tansy.spoke": False,
        "drain.tested": False, "drain.works": False, "drain.level": 0,
        "bridge.tested": False, "bridge.works": False, "bridge.span": 3, "bridge.support": 0,
        "soup.shared": False, "soup.lit": False, "newspaper.read_again": False,
    })
    for carrier, content in (("pigs", A("Pride", 4)), ("wolf", FOUNDATIONS + BRIDGES + A("WolfBuilder", 3)),
                             ("fox", A("WantCheese", 3) + A("Curiosity", 2)),
                             ("mira", A("Curiosity", 2)), ("tansy", A("Curiosity", 2)),
                             ("foundations", FOUNDATIONS), ("bridges", BRIDGES)):
        for name, weight in content.terms:
            state[f"{carrier}.meme.{name}"] = weight
    return World(entities, ("market", "creek", "shore", "brick", "worksite", "hill", "depot", "edge"),
                 state, validate)


def action(world, drama, name, actors, fn):
    return world.act(drama, name, actors, fn)


def opening(w, p):
    def run(t):
        t.require(t.get("cottage.occupant") == "wolf", "Wolf begins at home")
        t.set("soup.lit", True)
        t.set("valley.phase", 1)
    action(w, "opening", "light_the_soup_stove", ("wolf",), run)


def wind(w, p):
    def run(t):
        t.require(t.get("valley.wind") > t.get("straw.capacity"), "Wind exceeds the straw house's strength")
        t.set("straw.failed", True); t.set("straw.cause", "wind")
        t.embed("pigs", SCAPEGOAT)
        t.set("valley.phase", 2)
    action(w, "wind", "collapse_and_invent_accusation", ("pigs",), run)


def market(w, p):
    def run(t):
        t.absorb("pigs", "poster", terms=("BlameWolf", "Obey"))
        t.set("poster.printed", True)
        for child in ("mira", "tansy"):
            t.absorb("poster", child, terms=("BlameWolf", "Obey"))
        t.set("valley.reporting", True); t.set("valley.phase", 3)
    action(w, "market", "print_and_read_the_accusation", ("pigs", "mira", "tansy"), run)


def exile(w, p):
    def run(t):
        t.require(t.get("mira.meme.BlameWolf") + t.get("tansy.meme.BlameWolf") >= 6,
                  "The public accusation has reached the neighbors")
        t.move("wolf", "shore"); t.move("soup", "shore")
        t.set("soup.lit", False); t.set("cottage.occupant", "empty"); t.set("valley.phase", 4)
    action(w, "exile", "leave_the_creek", ("wolf",), run)


def rain(w, p):
    def run(t):
        t.require(t.get("valley.rain") > t.get("wood.footing"), "Rain defeats the wooden house's footing")
        t.require(t.get("wolf.location") == "shore", "Wolf is far away during the collapse")
        t.set("wood.failed", True); t.set("wood.cause", "mud")
        t.absorb("pigs", "newspaper", terms=("BlameWolf", "Obey"))
        t.set("newspaper.printed", True); t.set("valley.phase", 5)
    action(w, "rain", "repeat_the_story_after_a_second_failure", ("pigs",), run)


def occupation(w, p):
    def run(t):
        t.require(t.get("brick.load") > t.get("brick.footing"), "The brick wall has inadequate footing")
        t.set("brick.failed", True); t.set("brick.cause", "bad_foundation")
        t.move("pigs", "creek"); t.set("cottage.occupant", "pigs"); t.set("valley.phase", 6)
    action(w, "occupation", "occupy_the_absent_wolfs_cottage", ("pigs",), run)


def return_wolf(w, p):
    def run(t):
        t.move("pigs", "shore")
        t.require(t.get("pigs.location") == t.get("wolf.location"), "The pigs actually reach Wolf")
        t.move("wolf", "brick"); t.move("soup", "brick"); t.move("pigs", "creek")
        t.set("valley.whispers", True)
        t.set("wolf.free", False); t.set("wolf.coerced", True)
        t.set("valley.cottages_built", True)
        t.set("pigs.claims_authorship", True); t.set("valley.phase", 7)
    action(w, "return", "bring_wolf_back_under_coercion", ("pigs", "wolf"), run)


def fox(w, p):
    def run(t):
        for who in ("fox", "mira", "tansy", "wolf"):
            t.move(who, "worksite")
        t.require(t.get("fox.meme.WantCheese") > 0, "Fox has a reason to take the cheese")
        t.add("cheese.portions", -3); t.set("fox.took_cheese", True)
        if t.get("mira.witness_position"):
            t.observe("mira", "fox", "fox.took_cheese", "mira.saw_theft")
            t.embed("mira", A("Question", 1))
            t.set("mira.meme.BlameWolf", 0.0)
        t.set("pigs.blame_cheese", True)
        t.set("valley.phase", 8)
    action(w, "fox", "steal_cheese_under_the_wrong_picture", ("fox", "mira", "tansy"), run)


def whisper(w, p):
    def run(t):
        t.set("valley.whispers", True)
        t.embed("fox", A("StatusThreat", 2))
        t.move("fox", "creek")
        t.absorb("fox", "pigs", terms=("StatusThreat",))
        t.set("valley.phase", 9)
    action(w, "whisper", "turn_the_pigs_identity_story_against_them", ("fox", "pigs"), run)


def commission(w, p):
    def run(t):
        t.require(t.get("pigs.meme.Pride") * t.get("pigs.meme.StatusThreat") >= 6,
                  "Prestige and identity threat motivate the palace")
        t.set("pigs.commission", True)
        for obj in ("books", "foundations", "bridges"):
            t.move(obj, "hill")
        for who in ("pigs", "fox", "wolf", "mira", "tansy"):
            t.move(who, "hill")
        t.set("books.delivered", True)
        opened = t.get("books.shelf_policy") == "open"
        t.set("books.accessible", opened)
        t.set("foundations.accessible", opened)
        t.set("bridges.accessible", opened)
        t.set("valley.phase", 10)
    action(w, "commission", "buy_books_and_build_shelves", ("pigs", "fox", "wolf"), run)


def read_book(child, book):
    def perform(w, p):
        def run(t):
            t.require(t.get("books.accessible"), "Readers can reach the shelves")
            t.absorb(book, child, divisor=t.get(child + ".attention_divisor"))
            t.set(child + ".read", True)
        action(w, "read_" + child, "read_a_physical_book", (child,), run)
    return perform


def mentor(w, p):
    def run(t):
        t.require(t.get("wolf.teaching_available"), "Wolf has time to answer questions")
        for child, craft in (("mira", "DrainCraft"), ("tansy", "BridgeCraft")):
            if t.get(child + ".read") and (child == "mira" or t.get("valley.work_arrangement") == "shared"):
                # A short demonstration reinforces a little, not an entire book.
                t.absorb("wolf", child, divisor=8 / 3, terms=(craft,))
                t.set(child + ".mentored", True)
    action(w, "mentor", "answer_questions_at_the_workbench", ("wolf", "mira", "tansy"), run)


def practice(child, prop, craft):
    def perform(w, p):
        def run(t):
            t.require(t.get(child + ".read"), "The child has encountered the relevant instructions")
            t.require(t.get(child + ".location") == t.get(prop + ".location"), "The worker can reach the trial object")
            understood = t.get(child + ".meme." + craft) >= 1.5
            measure = prop + (".level" if prop == "drain" else ".support")
            t.set(measure, 3 if understood else 1)
            enough = t.get(measure) >= (2 if prop == "drain" else t.get("bridge.span"))
            t.set(prop + ".tested", True)
            t.set(prop + ".works", enough)
            if enough:
                t.set(child + ".skilled", True)
                t.embed(child, A("ProtectBooks", 2.5) + A("WolfBuilder", 1))
                t.set(child + ".meme.Obey", max(0.0, t.get(child + ".meme.Obey") - 1.5))
                if t.get("valley.work_arrangement") == "shared":
                    # Both see the work, but the observer does not inherit the skill.
                    other = "tansy" if child == "mira" else "mira"
                    t.require(t.get(child + ".location") == t.get(other + ".location"), "Helpers are present")
                    t.embed(child, A("SharedWork", 1))
                    t.embed(other, A("SharedWork", 1))
        action(w, "practice_" + prop, "test_" + prop + "_under_load", (child, "wolf"), run)
    return perform


def soup(w, p):
    def run(t):
        t.move("soup", "hill")
        t.set("soup.shared", True)
        t.embed("mira", A("WolfBuilder", 0.5))
    action(w, "soup", "share_lunch_with_the_builder", ("wolf", "mira"), run)


def repeat_paper(w, p):
    def run(t):
        t.move("newspaper", "hill")
        # Repetition influences obedience, not the established physical facts.
        for child in ("mira", "tansy"):
            t.absorb("newspaper", child, divisor=4, terms=("Obey",))
        t.set("newspaper.read_again", True)
    action(w, "paper", "bring_the_official_story_to_the_worksite", ("pigs", "mira", "tansy"), run)


def finish(w, p):
    def run(t):
        t.set("palace.roof", True); t.set("valley.phase", 11)
    action(w, "finish", "complete_the_palace", ("wolf", "mira", "tansy"), run)


def confrontation(w, p):
    def run(t):
        t.require(t.get("palace.roof"), "The opening happens in a completed building")
        count = 0
        coalition = True
        for child in ("mira", "tansy"):
            score = t.get(child + ".meme.ProtectBooks") + t.get(child + ".meme.SharedWork") - t.get(child + ".meme.Obey")
            speaks = t.get(child + ".skilled") and score >= 1
            t.set(child + ".spoke", speaks)
            count += int(speaks)
            coalition = coalition and speaks and t.get(child + ".meme.SharedWork") >= 1
        t.set("palace.dissenters", count); t.set("palace.coalition", coalition)
        t.set("valley.phase", 12)
    action(w, "confrontation", "order_the_books_removed_and_hear_the_response", ("pigs", "mira", "tansy"), run)


def ending(w, p):
    def run(t):
        if t.get("palace.coalition"):
            t.require(t.get("pigs.meme.Pride") > 0, "The pigs value public prestige enough to claim a gift")
            t.set("pigs.claims_gift", True)
            t.set("palace.outcome", "library"); t.set("palace.public", True)
            t.set("palace.owner", "valley")
            t.set("palace.occupant", "valley"); t.set("palace.title", "Library")
            t.set("foundations.owner", "valley"); t.set("bridges.owner", "valley")
            t.move("pigs", "brick")
            t.set("cottage.occupant", "wolf")
            t.set("wolf.coerced", False); t.set("wolf.free", True)
            t.move("wolf", "creek"); t.move("soup", "creek")
            t.set("wolf.home_restored", True); t.set("soup.lit", True)
        elif t.get("palace.dissenters"):
            t.set("palace.outcome", "night_school")
            t.require(t.get("books.accessible"), "A rescued book must be reachable")
            t.move("foundations", "brick")
            t.move("mira", "brick"); t.move("tansy", "brick"); t.move("wolf", "brick")
            t.move("soup", "brick"); t.set("soup.lit", True)
            # Custody changes; a clandestine rescue does not create legal ownership.
            t.set("books.accessible", False); t.set("palace.books_removed", True)
            t.set("bridges.accessible", False)
            t.move("pigs", "creek")
        else:
            t.set("palace.outcome", "closed_palace")
            t.set("books.accessible", False); t.set("palace.books_removed", True)
            t.set("foundations.accessible", False); t.set("bridges.accessible", False)
            t.move("wolf", "brick"); t.move("soup", "brick")
            t.set("soup.lit", False); t.move("pigs", "creek")
        t.set("valley.ended", True)
    action(w, "ending", "settle_the_hall_and_the_cottage", ("pigs", "wolf", "mira", "tansy"), run)


def library(params):
    phases = [opening, wind, market, exile, rain, occupation, return_wolf, fox, whisper, commission]
    names = ["opening", "wind", "market", "exile", "rain", "occupation", "return", "fox", "whisper", "commission"]
    dramas = [Microdrama(n, lambda s, i=i: s["valley.phase"] == i, fn)
              for i, (n, fn) in enumerate(zip(names, phases))]
    for child, book, prop, craft in (("mira", "foundations", "drain", "DrainCraft"),
                                     ("tansy", "bridges", "bridge", "BridgeCraft")):
        dramas.append(Microdrama("read_" + child,
            lambda s, c=child: s["valley.phase"] == 10 and s["books.accessible"] and not s[c + ".read"],
            read_book(child, book), 30, "read_and_absorb"))
        dramas.append(Microdrama("practice_" + prop,
            lambda s, c=child, o=prop: s["valley.phase"] == 10 and s[c + ".read"] and not s[o + ".tested"],
            practice(child, prop, craft), 10, "try_and_observe"))
    dramas.append(Microdrama("mentor", lambda s: s["valley.phase"] == 10 and s["wolf.teaching_available"] and s["mira.read"] and s["tansy.read"], mentor, 20, "teach"))
    dramas += [
        Microdrama("soup", lambda s: s["valley.phase"] == 10, soup, 10, "share"),
        Microdrama("paper", lambda s: s["valley.phase"] == 10, repeat_paper, 10, "repeat_claim"),
        Microdrama("finish", lambda s: s["valley.phase"] == 10 and
                   (not s["books.accessible"] or (s["drain.tested"] and s["bridge.tested"])), finish, 10),
        Microdrama("confrontation", lambda s: s["valley.phase"] == 11, confrontation, 10, "contest_claim"),
        Microdrama("ending", lambda s: s["valley.phase"] == 12, ending),
    ]
    return tuple(dramas)
