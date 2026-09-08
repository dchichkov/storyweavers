#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a historic shutter, friendship, and
problem solving.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[3]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402



def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    captain: object | None = None
    friend: object | None = None
    shutter: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "matey"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    captain: str = ""
    friend: str = ""
    place: str = ""
    ship_name: str = ""
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Scenario:
    key: str
    premise: str
    obstacle: str
    rushed_action: str
    consequence: str
    clue: str
    careful_action: str
    reveal: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


CAPTAIN_NAMES = ["Captain Mira", "Captain Bea", "Captain Tilda", "Captain Jory", "Captain Nia", "Captain Finn"]
FRIEND_NAMES = ["Pip", "Marn", "Lula", "Rory", "Sailor Sue", "Jeb"]
PLACES = [
    "the misty harbor",
    "the old lighthouse cove",
    "the moonlit dock",
    "the windy salt cliffs",
]
SHIP_NAMES = ["The Little Gull", "The Wobbly Wave", "The Barnacle Bell", "The Bright Plank"]
TELLING_MODES = ["arrival", "warning", "dialogue", "countdown", "memory", "mystery", "promise", "question"]

SCENARIOS = [
    Scenario(
        key="historic_shutter",
        premise="was visiting a historic harbor house where a shutter had been stuck for years",
        obstacle="a heavy shutter had slammed shut over the lighthouse room",
        rushed_action="yanked the shutter with a rope",
        consequence="the old latch cracked and a lantern went dark",
        clue="the shutter creaked in a rhythm that matched the bell buoy outside",
        careful_action="tapped the rhythm back with a small drum and gentle hands",
        reveal="the shutter was hiding a secret map to the safe route through the rocks",
        apology="admitted the rope had made the old wood hurt more",
        repair="oiled the hinges, mended the latch, and opened the room together",
        outcome="the lantern shone again and the safe route could be seen from the sea",
        lesson="kind problem solving can wake an old thing without breaking it",
        ending="the historic shutter stood open at last while the map fluttered like a happy sail",
    ),
    Scenario(
        key="treasure_window",
        premise="was searching for a treasure chart in an abandoned pirate office",
        obstacle="a shuttered window hid the only beam that could reveal the ink",
        rushed_action="pushed the window open with a cutlass hilt",
        consequence="dust burst up and the chart slipped behind a crate",
        clue="the dust sparkled where the sun touched a tiny painted fish on the frame",
        careful_action="slid the shutter aside inch by inch and let the beam land on the fish",
        reveal="the painted fish pointed straight to the chart drawer",
        apology="said the quick push had sent the clue tumbling away",
        repair="set the crate back, brushed the dust, and shared the chart with the crew",
        outcome="the treasure path glowed on the page and everyone cheered",
        lesson="the best answer comes from looking before grabbing",
        ending="the shutter opened wide while the chart shone gold on the captain's desk",
    ),
    Scenario(
        key="storm_signal",
        premise="was trying to guide a fishing boat home before a storm rolled in",
        obstacle="a crooked shutter on the signal tower kept the warning lamp from blinking",
        rushed_action="banged the shutter with a hook",
        consequence="the lamp swung loose and the warning flash went out",
        clue="the broken shutter only failed when the wind blew from the east",
        careful_action="held the board steady with a sail tie and a friend at each side",
        reveal="the hinge was bent, not broken, and only needed to be lined up",
        apology="confessed that the banged board had made the tower worse",
        repair="straightened the hinge, tied the brace, and restored the lamp",
        outcome="the warning flashed bright and the fishing boat reached harbor safely",
        lesson="two steady hands can do what one angry swing cannot",
        ending="the repaired shutter clicked once, and then the tower blinked like a happy eye",
    ),
    Scenario(
        key="hidden_lantern",
        premise="was helping a shipmate find a hidden lantern used by the harbor watch",
        obstacle="a rusty shutter blocked the lantern nook in the old fort",
        rushed_action="forced the shutter open with a crowbar",
        consequence="the fort floor groaned and a powder crate tipped sideways",
        clue="a thin line of clean salt showed where the shutter had been resting all along",
        careful_action="lifted the shutter gently and cleared the salt from the sill",
        reveal="the lantern had been carefully tucked behind the shutter for safekeeping",
        apology="said the crowbar had nearly ruined the watch room",
        repair="set the lantern back, fixed the crate, and closed the fort with care",
        outcome="the harbor watch lit the lantern and kept the night safe",
        lesson="a hidden thing is not always a lost thing",
        ending="the old fort glimmered while the shutter rested open like a calm smile",
    ),
    Scenario(
        key="chorus_porthole",
        premise="was hosting a singing contest for dock children on the quarterdeck",
        obstacle="a shutter over the porthole jammed the sea breeze from reaching the singers",
        rushed_action="swung the shutter wide with one shove",
        consequence="the wind blew papers everywhere and the contest fell apart",
        clue="the porthole hummed when the shutter was half closed and the children sang softly",
        careful_action="matched the opening to the song's rhythm instead of forcing it",
        reveal="the shutter worked like a music box door and made the best echo at half swing",
        apology="told the children the shove had spoiled their game",
        repair="set the shutter to the right angle and handed the songs back one by one",
        outcome="the chorus rang clear and the crowd clapped in time",
        lesson="a small adjustment can solve a problem better than a big push",
        ending="the porthole shutter stayed half open while the sea breeze kept the song alive",
    ),
    Scenario(
        key="map_room",
        premise="was repairing a map room in a pirate museum before visitors arrived",
        obstacle="a painted shutter hid the oldest map from the morning light",
        rushed_action="scrubbed the shutter clean with salty water",
        consequence="the paint streaked and the map colors bled a little",
        clue="one faded star appeared only when the shutter was angled toward dawn",
        careful_action="used a soft cloth and measured the light with a compass",
        reveal="the shutter itself carried a painted route made by the first harbor captain",
        apology="owned the careless scrubbing and promised to fix the paint",
        repair="restored the color, adjusted the shutter angle, and framed the route safely",
        outcome="the museum opened with the true historic route shining for everyone",
        lesson="careful tools protect both memory and friendship",
        ending="the museum's shutter glowed with restored color and the old route slept safely behind glass",
    ),
    Scenario(
        key="reef_beacon",
        premise="was guiding a friend across a reef where the tide changed fast",
        obstacle="a bent shutter on the reef beacon blocked the light from the sea lane",
        rushed_action="knocked the shutter flat with a boat pole",
        consequence="the beacon flashed into the rocks and the boat had to stop",
        clue="the beam pointed true whenever the shutter was held at a slant",
        careful_action="wedge-shimmed the shutter with driftwood and checked the line by eye",
        reveal="the beacon wanted a slanted opening to steer the light between the stones",
        apology="said the flat knock had pointed the beam the wrong way",
        repair="set the driftwood brace, relit the beacon, and marked the safe path",
        outcome="the boat slipped through the reef and reached calm water",
        lesson="not every broken-looking thing wants to be flattened",
        ending="the reef beacon blinked through its crooked shutter like a pirate wink",
    ),
    Scenario(
        key="parrot_cabin",
        premise="was looking for a missing parrot in the captain's cabin",
        obstacle="a shuttered cupboard trapped the parrot's loud squawk inside",
        rushed_action="flung the cupboard door open",
        consequence="a stack of cups crashed and the parrot darted higher",
        clue="the squawk answered every knock from the cupboard's back wall",
        careful_action="knocked softly and opened the shutter only after the bird calmed",
        reveal="the parrot had hidden behind the shutter with a shiny key in its beak",
        apology="laughed and apologized for the noisy scare",
        repair="righted the cups, thanked the parrot, and used the key to open the chest",
        outcome="the chest held the missing sail ties and the crew could leave port",
        lesson="friendship grows when you treat even a noisy helper kindly",
        ending="the parrot perched on the open shutter while the crew tied the last sail",
    ),
    Scenario(
        key="harbor_bell",
        premise="was helping the harbor keeper ring a bell for the evening tide",
        obstacle="a barnacled shutter jammed the bell rope in the old bell house",
        rushed_action="pulled the rope hard",
        consequence="the rope snapped back and the bell rang wrong",
        clue="the bell sounded right only when the shutter let in the wind from the sea",
        careful_action="opened the shutter just enough and tied the rope in a smoother loop",
        reveal="the bell house needed the sea wind to move the clapper properly",
        apology="said the hard pull had nearly torn the rope in two",
        repair="spliced the rope and set the shutter to catch the wind",
        outcome="the tide bell rang clear and the boats knew it was time to dock",
        lesson="sometimes the best fix is to work with the wind instead of against it",
        ending="the barnacled shutter swayed as the harbor bell sang across the water",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate Tale storyworld with friendship and problem solving.")
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
    ap.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    ap.add_argument("--telling-mode", choices=TELLING_MODES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != captain])
    place = getattr(args, "place", None) or rng.choice(PLACES)
    ship_name = getattr(args, "ship_name", None) or rng.choice(SHIP_NAMES)
    scenario = getattr(args, "scenario", None) or rng.choice(SCENARIOS).key
    telling_mode = getattr(args, "telling_mode", None) or rng.choice(TELLING_MODES)
    return StoryParams(captain=captain, friend=friend, place=place, ship_name=ship_name, scenario=scenario, telling_mode=telling_mode)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("theme", "pirate_tale"),
        asp.fact("feature", "Friendship"),
        asp.fact("feature", "Problem_Solving"),
        asp.fact("seed_word", "historic"),
        asp.fact("seed_word", "shutter"),
        asp.fact("object", "historic_shutter"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
feature_ok(F) :- feature(F).
seed_ok(W) :- seed_word(W).
problem_world :- feature("Problem_Solving"), feature("Friendship"), object(historic_shutter).
#show feature/1.
#show seed_word/1.
#show object/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show feature/1."))
    feats = sorted(set(asp.atoms(model, "feature")))
    wanted = [("Friendship",), ("Problem_Solving",)]
    if feats != wanted:
        print("MISMATCH: ASP feature facts are wrong.")
        print(feats)
        return 1
    print("OK: ASP facts include the required features.")
    return 0


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), _safe_lookup(SCENARIOS, 0))
    world = World(params=params)
    captain = world.add(Entity(id=params.captain, type="captain", label=params.captain, location="deck", memes={"friendship": 0.5}))
    friend = world.add(Entity(id=params.friend, type="matey", label=params.friend, location="deck", memes={"friendship": 0.7}))
    shutter = world.add(Entity(id="historic_shutter", type="shutter", label="historic shutter", location=params.place, meters={"stuck": 1.0}, memes={"mystery": 1.0}))

    world.say(f"At {params.place}, Captain {params.captain} and {params.friend} sailed aboard {params.ship_name}, where an old tale led them to {scenario.premise}.")
    world.say(f"The trouble began when {scenario.obstacle}.")
    world.say(f'"That looks stubborn," {params.friend} said. "Aye," Captain {params.captain} replied, "but not impossible."')

    world.para()
    world.say(f"At first, {params.friend} {scenario.rushed_action}, and {scenario.consequence}.")
    world.say(f'"Easy now," Captain {params.captain} said. "Let us solve it proper-like."')
    world.say(f"They paused and noticed that {scenario.clue}.")

    world.para()
    world.say(f"Captain {params.captain} {scenario.careful_action}.")
    world.say(f"With that patient trick, they learned that {scenario.reveal}.")
    world.say(f'"I was wrong to rush," {params.friend} said. "{scenario.apology}."')
    world.say(f'"We fix it together," Captain {params.captain} answered. "That is what mates do."')
    world.say(f"So the pair {scenario.repair}, and {scenario.outcome}.")

    world.para()
    world.say(f"In the end, {scenario.lesson}, and their friendship grew steadier than the tide.")
    world.say(f"The story closed with this sight: {scenario.ending}.")

    captain.memes["friendship"] = 0.95
    friend.memes["friendship"] = 0.95
    shutter.meters["stuck"] = 0.0
    shutter.meters["open"] = 1.0
    shutter.memes["understood"] = 1.0
    world.facts.update({"scenario": scenario.key, "repaired": True, "historic": True, "shutter": True})

    prompts = [
        f"Write a pirate tale about Captain {params.captain} and {params.friend} solving a problem with a historic shutter.",
        f"Tell a child-friendly story where friendship and problem solving help fix a stubborn shutter at {params.place}.",
        f"Write a short pirate adventure aboard {params.ship_name} with a clear beginning, turn, and ending image.",
    ]
    story_qa = [
        QAItem(
            question="What problem did the crew face?",
            answer=f"They faced the problem that {scenario.obstacle}. It blocked the work they needed to do at {params.place}.",
        ),
        QAItem(
            question="How did the crew solve it?",
            answer=f"They stopped rushing, noticed that {scenario.clue}, and used careful problem solving to repair the shutter.",
        ),
        QAItem(
            question="Why did {friend} apologize?".replace("{friend}", params.friend),
            answer=f"{params.friend} apologized because rushing made the trouble worse. The apology helped the friends fix it together.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, {scenario.outcome}, and the friendship between Captain {params.captain} and {params.friend} was stronger.",
        ),
    ]
    world_qa = [
        QAItem(question="What does friendship mean in this storyworld?", answer="Friendship means helping each other, listening, and staying kind when a problem gets hard."),
        QAItem(question="What does problem solving mean?", answer="Problem solving means slowing down, noticing clues, and choosing a careful action that fixes the trouble."),
        QAItem(question="What is a shutter?", answer="A shutter is a board or panel that can open and close over a window, lamp, or room."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for ent in sample.world.entities.values():
            bits = []
            if ent.location:
                bits.append(f"location={ent.location}")
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            print(f"  {ent.id}: {ent.type} {' '.join(bits)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show object/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(captain="Captain Mira", friend="Pip", place="the misty harbor", ship_name="The Little Gull", seed=101, scenario="historic_shutter", telling_mode="arrival"),
            StoryParams(captain="Captain Bea", friend="Lula", place="the old lighthouse cove", ship_name="The Barnacle Bell", seed=202, scenario="reef_beacon", telling_mode="dialogue"),
            StoryParams(captain="Captain Jory", friend="Rory", place="the moonlit dock", ship_name="The Bright Plank", seed=303, scenario="harbor_bell", telling_mode="mystery"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            attempt_seed = base_seed + i
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.captain} and {p.friend} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
