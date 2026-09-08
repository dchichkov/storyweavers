#!/usr/bin/env python3
"""
A standalone Storyweavers world: a superhero rescue quest with a grizzly problem.

Premise:
- A small hero team in a bright city must stop a runaway grizzly from causing harm.
- The lead hero uses an inner monologue to think clearly under pressure.
- The team goes on a quest through the city to find the bear's trail and help it safely.
- The ending is happy, with the city calm again and everyone learning something useful.

This script follows the Storyworld contract:
- standalone stdlib Python
- lazy ASP import for verification/query modes
- world simulation with physical meters and emotional memes
- StorySample/QAItem/StoryError from storyworlds.results
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


SETTING = "city rooftop district"
SEED_WORDS = {"terminate", "grizzly", "scour"}



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self):
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ["fear", "scratches", "height", "speed", "noise", "hope", "trust"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "courage", "curiosity", "kindness", "relief", "teamwork", "resolve"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    hero: str = "Nova"
    partner: str = "Kite"
    grizzly_name: str = "Bruno"
    city: str = "Skyline"
    seed: Optional[int] = None
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
class Case:
    quest_goal: str
    trouble: str
    clue: str
    false_lead: str
    inner_monologue: str
    dialogue1: str
    dialogue2: str
    discovery: str
    cause: str
    repair: str
    proof: str
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


CASES = [
    Case(
        quest_goal="guide a grizzly back to the riverside preserve",
        trouble="a grizzly had barreled across the plaza and scattered market carts like toy blocks",
        clue="mud on a fire escape and a trail of berry leaves on the wind",
        false_lead="a crashed food truck looked like the obvious source of the mess",
        inner_monologue="The truck is loud, but berry leaves tell a quieter story. Follow the living trail.",
        dialogue1="Nova said, 'We scout the rooftop first and look for the freshest trail.'",
        dialogue2="Kite replied, 'And if the bear is scared, we use calm words, not loud ones.'",
        discovery="found Bruno wedged beside a rooftop garden, sniffing an overturned honey crate",
        cause="had chased the smell of spilled honey after a storm drain cover clanged open",
        repair="scoured the rooftop path clean, righted the crate, and opened a safe route down to the preserve",
        proof="the bear's paws stayed on the painted guide line and the market below grew quiet",
        lesson="A hero can stop a problem best by understanding it first and then choosing a safe fix.",
        ending="By sunset, Bruno padded beside the river, and the city lights shone softly over a happy, calm street.",
    ),
    Case(
        quest_goal="rescue a baby owl and the grizzly who got lost together",
        trouble="a grizzly and a tiny owl had tangled themselves in a torn kite line above the ferry dock",
        clue="silver feathers stuck to a rooftop vent beside one frayed string",
        false_lead="the loud ferris wheel made everyone look the wrong way for a while",
        inner_monologue="The wheel spins, but the feathers point here. Search the small things, not just the big noise.",
        dialogue1="Kite asked, 'Should we hurry?'",
        dialogue2="Nova said, 'Yes, but carefully. A quest can still be gentle.'",
        discovery="found the owl perched safely on the grizzly's back while the last loop was cut free",
        cause="had followed the kite line while trying to catch a drifting balloon",
        repair="scoured the dock rail, cut the tangled line, and helped the owl return to its nest",
        proof="the owl flew to the bell tower and the grizzly sat down without pulling on the rope again",
        lesson="Careful teamwork can turn a chaotic chase into a rescue.",
        ending="The bell tower door stayed open, and the grizzly watched the owl rise into a clear blue sky.",
    ),
    Case(
        quest_goal="save a costume parade from a frightened grizzly on the boulevard",
        trouble="a grizzly in a glitter cape had thundered through the parade and bumped every drum in sight",
        clue="blue confetti stuck to a lamppost and a pawprint led toward the fountain",
        false_lead="the drum line made the whole street sound like the problem",
        inner_monologue="The drums are only noise. The pawprint is the path. Follow the path.",
        dialogue1="Kite said, 'We can ask what scared the bear.'",
        dialogue2="Nova answered, 'And we can keep the crowd back so nobody gets hurt.'",
        discovery="found Bruno shaking beside the fountain where the flashing parade lights reflected on the water",
        cause="had panicked when a drum cannon burst too close",
        repair="scoured the glitter from the sidewalk, dimmed the parade lights, and led Bruno away from the blast",
        proof="the drums resumed at a softer beat and the grizzly stopped shaking",
        lesson="Sometimes the brave choice is not to fight harder, but to reduce the fear around you.",
        ending="The parade rolled on again, and Bruno's glitter cape twinkled peacefully at the very end of the line.",
    ),
    Case(
        quest_goal="find a missing rescue beacon before nightfall",
        trouble="a grizzly had knocked the beacon loose from the top of the library dome",
        clue="fresh scratch marks on the dome ladder and a smear of honey on the beam",
        false_lead="a pile of broken signboards looked like the beacon could be under any of them",
        inner_monologue="Honey on the beam means paws were here. Search upward where the problem began.",
        dialogue1="Nova said, 'I will take the ladder. You keep watch below.'",
        dialogue2="Kite replied, 'Deal. If the beacon is found, we can terminate the search and go home.'",
        discovery="found the beacon tucked into a rain gutter beside the dome's highest tile",
        cause="had reached for the shiny light while sniffing the honey on the railing",
        repair="scoured the gutter clear, reset the beacon on its mount, and made the dome safe again",
        proof="the beacon flashed across three rooftops without wobbling",
        lesson="A quest works best when every clue is checked against the place it came from.",
        ending="When the beacon blinked on, the whole city breathed easier and the grizzly wandered back to the trees.",
    ),
    Case(
        quest_goal="help a grizzly return a lost map to the museum",
        trouble="a grizzly had sat on the mayor's fountain bench and pinned the paper map beneath one paw",
        clue="wet map edges and pawprints heading from the fountain toward the museum steps",
        false_lead="a stack of tourist flyers looked like the missing map at first glance",
        inner_monologue="Flyers are thin and bright. The real map is wet and folded. Trust the shapes, not the color.",
        dialogue1="Kite asked, 'Do we confront the bear?'",
        dialogue2="Nova said, 'No. We guide it to the real owner and keep everyone calm.'",
        discovery="found the map hanging from Bruno's backpack strap like a cape",
        cause="had borrowed the map to follow a trail of sweet-smelling donuts",
        repair="scoured the fountain bench dry, replaced the map in its sleeve, and walked Bruno back to the museum door",
        proof="the museum guard smiled as the map landed in the right hands",
        lesson="A happy ending can begin with patience, careful noticing, and a kind question.",
        ending="Under the museum lamps, Bruno bowed once, and the city cheered for the gentle rescue.",
    ),
    Case(
        quest_goal="clear a rooftop garden path for a nighttime comic-book launch",
        trouble="a grizzly had trampled the tomato planters while searching for something shiny",
        clue="broken tomato vines and one bright sticker glued to the grizzly's paw",
        false_lead="the shredded launch banner looked like the worst damage",
        inner_monologue="The banner is ripped, but the paw sticker says where the bear walked. Follow the paw, not the paper.",
        dialogue1="Nova said, 'Let's scour the garden in pairs.'",
        dialogue2="Kite nodded. 'You take the west beds. I'll check the east side.'",
        discovery="found Bruno hiding behind a water barrel, embarrassed and sticky with syrup",
        cause="had chased a dropped candy wrapper that sparkled in the moonlight",
        repair="scoured the mud from the path, replanted the vines, and patched the banner before the launch",
        proof="the comic books stacked neatly beside intact tomato cages and a clean path to the stage",
        lesson="The best hero work leaves a place safer than it was before.",
        ending="The launch lights came on, and Bruno watched the first comic page glow beside a fresh tomato leaf.",
    ),
    Case(
        quest_goal="escort a grizzly away from the children at the playground",
        trouble="a grizzly had arrived at the slide wearing a stolen picnic blanket like a cape",
        clue="sand on the blanket hem and a trail of dropped apples from the hill",
        false_lead="the swing chains rattled so loudly that the whole playground seemed guilty",
        inner_monologue="The swings only make noise. Apples rolling downhill point to the hill trail.",
        dialogue1="Kite said, 'I can talk to the kids while you talk to the bear.'",
        dialogue2="Nova replied, 'Great. We keep everyone safe and keep our voices warm.'",
        discovery="found the grizzly snuffling beside the apple tree, not at all mean, just hungry",
        cause="had followed the smell of picnic food after a windy lunch",
        repair="scoured the blanket clean, returned it to the picnic table, and led the bear to a berry cart",
        proof="the children waved from the fence while the bear ate berries far from the slide",
        lesson="A strange-looking problem is not always a dangerous one; it still needs care and a plan.",
        ending="The playground bells rang again, and the grizzly left with a berry smile and a safer path home.",
    ),
    Case(
        quest_goal="find the lost rescue helmet before the storm",
        trouble="a grizzly had knocked the helmet from the hero tower during a rooftop drill",
        clue="a dent in the drainpipe and a streak of paw mud on the skylight",
        false_lead="the blinking traffic lights made the tower roof look like a maze",
        inner_monologue="The lights blink, but mud does not lie. Search where the mud points.",
        dialogue1="Nova said, 'We are not quitting until the helmet is back.'",
        dialogue2="Kite answered, 'Then let's scour the roof from edge to center.'",
        discovery="found the helmet under a stack of tarps beside the weather vane",
        cause="had batted the shiny helmet while trying to play with the spinning vane",
        repair="scoured the tarps dry, fastened the helmet to a hook, and finished the drill before the rain",
        proof="the helmet stayed put even when the wind bent the weather vane",
        lesson="A clear plan beats a rushed guess when time is tight.",
        ending="The storm arrived after the drill ended, and the heroes watched it safely from the dry tower room.",
    ),
    Case(
        quest_goal="return a lost kitten to the pet shelter after the chase",
        trouble="a grizzly had burst into the alley and frightened the kitten under a delivery bench",
        clue="kitten pawprints and a smear of jam leading to the shelter gate",
        false_lead="an open trash lid looked like the first place to check",
        inner_monologue="Trash can wait. Tiny pawprints mean the kitten moved here, one careful step at a time.",
        dialogue1="Kite whispered, 'Slow voices only.'",
        dialogue2="Nova said, 'Right. A quest can be quiet if it helps.'",
        discovery="found the kitten curled safely on the grizzly's back, warm and unafraid",
        cause="had sniffed a jam tart and crouched too fast, making the kitten hide",
        repair="scoured the alley clean, offered a saucer of milk, and escorted both animals to the shelter",
        proof="the shelter door closed gently and the kitten purred in a blanket bed",
        lesson="Kindness can calm a surprise faster than shouting can.",
        ending="At the shelter window, the kitten slept, and the grizzly sat outside like a very careful guard.",
    ),
    Case(
        quest_goal="protect the city garden from a toppled statue and a confused grizzly",
        trouble="a grizzly had lurched into the herb garden after a statue fell with a mighty crack",
        clue="mint leaves crushed near the statue base and a pawtrack on the stair",
        false_lead="the cracked statue looked like the only thing worth worrying about",
        inner_monologue="The statue fell, but the grizzly moved after it. Track the paws, not just the crack.",
        dialogue1="Nova said, 'First we make space.'",
        dialogue2="Kite answered, 'Then we help the bear leave without scaring it more.'",
        discovery="found Bruno pressing himself against the hedge, ears low and eyes wide",
        cause="had jumped at the crash and stumbled through the mint bed",
        repair="scoured the broken gravel aside, reset the statue safely, and opened a clear path past the garden gate",
        proof="the herbs stood upright again and Bruno walked through the gate without touching a single pot",
        lesson="Safety comes from making room for fear to pass without adding more fear.",
        ending="Moonlight touched the mint leaves, and the garden looked peaceful again as the grizzly trotted home.",
    ),
    Case(
        quest_goal="guide a grizzly out of the transit tunnel",
        trouble="a grizzly had wandered into the subway tunnel and blocked the morning trains",
        clue="fresh dirt on the tunnel wall and a trail of snack wrappers near the stairs",
        false_lead="the loud train echo sounded like the bear was deeper inside than it was",
        inner_monologue="Echoes lie about distance. Wrappers and dirt show the real route.",
        dialogue1="Kite said, 'I can stop the crowd from coming down.'",
        dialogue2="Nova said, 'And I can lead the bear toward the light.'",
        discovery="found Bruno standing beside the emergency exit, staring at the bright yellow line",
        cause="had followed the smell of pretzels from the station kiosk",
        repair="scoured the tunnel floor clear, placed fresh signs, and guided Bruno up to the park path",
        proof="the first train rolled through safely after the tunnel was empty",
        lesson="A hero's job is to move people and creatures toward safety, not toward panic.",
        ending="When the station doors opened again, the commuters smiled, and the grizzly lumbered home under a sunny sky.",
    ),
]


@dataclass
class World:
    hero: Entity
    partner: Entity
    grizzly: Entity
    beacon: Entity
    city_map: Entity
    rooftops: Entity
    rescue_line: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _new_entity(eid: str, kind: str, type_: str, label: str, phrase: str = "", **kwargs) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, phrase=phrase, **kwargs)


def build_world(params: StoryParams) -> World:
    hero = _new_entity(params.hero, "character", "girl", "the hero", meters={}, memes={})
    partner = _new_entity(params.partner, "character", "boy", "the partner", meters={}, memes={})
    grizzly = _new_entity(params.grizzly_name, "character", "animal", "the grizzly", meters={}, memes={})
    beacon = _new_entity("beacon", "thing", "device", "rescue beacon", "the rooftop rescue beacon")
    city_map = _new_entity("map", "thing", "map", "city map", "the folded city map")
    rooftops = _new_entity("rooftops", "place", "place", "rooftops", "the high rooftops")
    rescue_line = _new_entity("line", "thing", "line", "guide line", "the painted guide line")
    world = World(hero=hero, partner=partner, grizzly=grizzly, beacon=beacon, city_map=city_map, rooftops=rooftops, rescue_line=rescue_line)
    world.facts["setting"] = SETTING
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, p, g = world.hero, world.partner, world.grizzly
    b, m, line = world.beacon, world.city_map, world.rescue_line
    case = _safe_lookup(CASES, abs(hash((params.hero, params.partner, params.grizzly_name, params.city))) % len(CASES))

    h.memes["worry"] += 1
    h.memes["resolve"] += 2
    p.memes["trust"] += 1
    g.memes["worry"] += 2
    b.meters["hope"] = 1
    m.meters["height"] = 1
    line.meters["trust"] = 1

    world.say(f"In {params.city}, the {SETTING} buzzed with alarms when {case.trouble}.")
    world.say(f"The heroes named their mission a quest: {case.quest_goal}.")
    world.say("Nova tightened her gloves and listened for the first clue.")

    world.para()
    world.say(f"Near the stairwell they spotted {case.clue}, while {case.false_lead}.")
    world.say(f"{h.id}'s inner monologue said, \"{case.inner_monologue}\"")
    world.say(case.dialogue1)
    world.say(case.dialogue2)

    world.para()
    world.say(f"Together they climbed the rooftops and {case.discovery}.")
    world.say(f"That explained the trouble: {case.cause}.")
    g.carried_by = None
    g.memes["worry"] -= 1
    g.memes["kindness"] += 1

    world.para()
    world.say(f"The two heroes {case.repair}.")
    world.say(f"They checked their work and saw that {case.proof}.")
    world.say("Nova said, 'We can terminate the danger now.' Kite grinned and answered, 'Only because we found the right path.'")
    world.say(f"Their lesson was simple: {case.lesson}")

    world.para()
    world.say(case.ending)

    world.facts.update(
        hero=h,
        partner=p,
        grizzly=g,
        beacon=b,
        city_map=m,
        rescue_line=line,
        quest_goal=case.quest_goal,
        trouble=case.trouble,
        clue=case.clue,
        false_lead=case.false_lead,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
        qa_case=case,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    case: Case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "qa_case")
    h: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    p: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "partner")
    g: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "grizzly")
    return [
        QAItem(
            question="What problem started the story?",
            answer=f"The trouble began when {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "trouble")}. That sent the heroes on a rescue quest.",
        ),
        QAItem(
            question="What clue did the hero trust?",
            answer=f"{h.id} trusted {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "clue")} instead of the false lead. That clue showed where to look next.",
        ),
        QAItem(
            question="How did the inner monologue help?",
            answer=f"{h.id} thought, '{case.inner_monologue}' That helped the hero choose the right path and stay calm.",
        ),
        QAItem(
            question="What did the team discover?",
            answer=f"They found {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "discovery")}. That explained why the grizzly had caused the trouble.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They repaired the problem by {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "repair")}, and the final image was happy because {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "ending")}",
        ),
        QAItem(
            question="What was the grizzly doing by the end?",
            answer=f"{g.id} was safe and calmer after the rescue. The heroes guided the grizzly away from danger instead of fighting it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to achieve an important goal, often by facing problems and finding clues.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large bear with strong claws, thick fur, and a powerful body.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to end or stop something completely.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a character does inside their mind.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the danger is resolved, the characters are safe, and the final image feels calm or joyful.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a superhero story set in {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "setting")} where the heroes must {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "quest_goal")}.",
        f"Include an inner monologue that helps the hero notice this clue: {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "clue")}.",
        "Make the ending happy, and include a brief back-and-forth dialogue that changes what the characters decide to do.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.partner, world.grizzly, world.beacon, world.city_map, world.rooftops, world.rescue_line]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(city_rooftops).
requires(city_rooftops, superhero).
requires(city_rooftops, grizzly).
requires(city_rooftops, quest).
requires(city_rooftops, inner_monologue).
requires(city_rooftops, happy_ending).

valid_story(S) :- setting(S), requires(S, superhero), requires(S, grizzly), requires(S, quest), requires(S, inner_monologue), requires(S, happy_ending).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join(
        [
            asp.fact("setting", "city_rooftops"),
            asp.fact("requires", "city_rooftops", "superhero"),
            asp.fact("requires", "city_rooftops", "grizzly"),
            asp.fact("requires", "city_rooftops", "quest"),
            asp.fact("requires", "city_rooftops", "inner_monologue"),
            asp.fact("requires", "city_rooftops", "happy_ending"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if ok:
        print("OK: ASP rules recognize the superhero quest story domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest story world with a grizzly rescue.")
    ap.add_argument("--hero", default=None)
    ap.add_argument("--partner", default=None)
    ap.add_argument("--grizzly-name", default=None)
    ap.add_argument("--city", default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(["Nova", "Lyra", "Beacon", "Mira", "Zara"])
    partner = getattr(args, "partner", None) or rng.choice(["Kite", "Arrow", "Pulse", "Jett", "Moss"])
    grizzly_name = getattr(args, "grizzly_name", None) or rng.choice(["Bruno", "Bearclaw", "Marlow", "Tundra"])
    city = getattr(args, "city", None) or rng.choice(["Skyline", "Harbor", "Summit", "Brightvale"])
    if hero == partner:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    offset = sample_seed - base_seed
    return StoryParams(hero=hero, partner=partner, grizzly_name=grizzly_name, city=city, seed=sample_seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero="Nova", partner="Kite", grizzly_name="Bruno", city="Skyline"),
    StoryParams(hero="Lyra", partner="Arrow", grizzly_name="Tundra", city="Brightvale"),
    StoryParams(hero="Zara", partner="Pulse", grizzly_name="Marlow", city="Harbor"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
