#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/parody_column_quest_bravery_myth.py
===================================================================

A standalone storyworld for a small mythic quest parody: a young seeker wants
to climb a sacred column, prove bravery, and retrieve a lost sign of the quest.
The tension is whether the seeker uses showy, unsafe shortcuts or a careful,
brave method with a helper and a proper ritual tool. The ending shows what
changed in the world: the column is climbed, the token is recovered, and the
parody becomes a real quest rather than a foolish stunt.

This world keeps a myth-like tone, but the simulated domain is small and concrete:
a chamber, a column, a quest token, a helper, and a test of bravery.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "sister", "woman"}
        male = {"boy", "father", "king", "brother", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    column_desc: str
    challenge: str
    audience: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    style: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_doubt(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes["showy"] >= THRESHOLD and ("doubt", "hero") not in world.fired:
        world.fired.add(("doubt", "hero"))
        hero.memes["fear"] += 1
        out.append("__doubt__")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    sig = ("brave", hero.id)
    if sig in world.fired:
        return out
    if hero.memes["bravery"] >= 1 and helper.memes["resolve"] >= 1:
        world.fired.add(sig)
        hero.memes["confidence"] += 1
        out.append("__brave__")
    return out


def _r_recover(world: World) -> list[str]:
    out: list[str] = []
    token = world.entities.get("token")
    if not token:
        return out
    sig = ("recover", token.id)
    if sig in world.fired:
        return out
    if token.meters["held"] >= THRESHOLD:
        world.fired.add(sig)
        token.meters["found"] = 1
        out.append("__recover__")
    return out


CAUSAL_RULES = [Rule("doubt", "social", _r_doubt), Rule("brave", "social", _r_brave), Rule("recover", "physical", _r_recover)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(quest: QuestItem, setting: Setting) -> bool:
    return "column" in quest.tags and "myth" in setting.tags and quest.id in QUESTS and setting.id in SETTINGS


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_contained(response: Response, danger: int) -> bool:
    return response.power >= danger


def tell(setting: Setting, quest: QuestItem, helper: Helper, response: Response,
         hero_name: str = "Ari", hero_gender: str = "boy", parent_type: str = "mother",
         seed: Optional[int] = None) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="quester", traits=["small", "bold"]))
    elder = world.add(Entity(id="Elder", kind="character", type=parent_type, role="elder"))
    guide = world.add(Entity(id=helper.id, kind="character", type="woman" if helper.id in {"Mira", "Nia"} else "man", role="helper", label=helper.label))
    column = world.add(Entity(id="column", type="thing", label="the column"))
    token = world.add(Entity(id="token", type="thing", label=quest.label))
    hero.memes["bravery"] = 1.0
    hero.memes["showy"] = 1.0
    guide.memes["resolve"] = 1.0
    world.facts["setting"] = setting
    world.facts["quest"] = quest
    world.facts["helper"] = helper
    world.facts["response"] = response
    world.facts["column"] = column
    world.facts["token"] = token

    world.say(f"In {setting.place}, under a {setting.mood} sky, {hero.id} came to {setting.column_desc}.")
    world.say(f"The old folk said the column guarded {quest.phrase}, and only true bravery could bring it home.")
    world.para()
    world.say(f'{hero.id} laughed at the tale like a parody of the old hero songs. "I can do it fast," {hero.id} said, and pointed at the column.')
    world.say(f'{guide.id} frowned and spoke softly: "{hero.id}, this is no game. The quest needs courage, not a foolish boast."')
    if hero.memes["showy"] >= THRESHOLD:
        hero.memes["defiance"] += 1
    danger = 1
    if hero.memes["defiance"] >= THRESHOLD and helper.power >= 1:
        world.say(f'But {hero.id} listened to {guide.id}, breathed once, and took the rope instead of a risky leap.')
        world.say(f'Together they climbed slowly, one hand at a time, while {setting.audience} watched in silence.')
        token.meters["held"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(f"{guide.id} placed {quest.phrase} in {hero.id}'s hands, and the chamber felt brighter than before.")
        world.say(f'{hero.id} bowed to {elder.label_word if elder.label else "the elder"} and said, "Bravery is not shouting. Bravery is doing the right climb."')
    else:
        hero.memes["bravery"] += 1
        token.meters["held"] += 1
        if is_contained(response, danger):
            world.say(f'{hero.id} chose the careful way after all. {helper.id} gave {response.text.replace("{token}", quest.label)}.')
            world.para()
            world.say(f'{hero.id} reached the top, and the quest was complete without a tumble.')
        else:
            world.say(f'{hero.id} tried a showy leap, but {response.fail.replace("{token}", quest.label)}.')
            world.para()
            world.say(f'Even then, {guide.id} climbed after {hero.id}, and the pair finished the quest with scraped knees and a steadier heart.')
        propagate(world, narrate=False)
    world.facts.update(hero=hero, elder=elder, column=column, token=token, setting=setting, quest=quest, helper=helper, outcome="completed")
    return world


SETTINGS = {
    "mythic_hall": Setting("mythic_hall", "the Hall of Echoes", "golden", "a tall column of white stone", "a quest of brave truth", "the gathered people", tags={"myth"}),
    "sun_temple": Setting("sun_temple", "the Sun Temple", "bright", "a carved column wrapped in ivy", "a quest of brave truth", "the waiting crowd", tags={"myth"}),
    "moon_court": Setting("moon_court", "the Moon Court", "silver", "a round column of moonstone", "a quest of brave truth", "the quiet crowd", tags={"myth"}),
}

QUESTS = {
    "parody_scroll": QuestItem("parody_scroll", "the parody scroll", "the parody scroll", "lift the parody scroll from the top", {"parody", "column", "quest"}),
    "copper_ring": QuestItem("copper_ring", "the copper ring", "the copper ring", "bring the ring home from the column", {"column", "quest"}),
    "bright_banner": QuestItem("bright_banner", "the bright banner", "the bright banner", "carry the banner down from the high column", {"column", "quest"}),
}

HELPERS = {
    "Mira": Helper("Mira", "the wise guide", "a wise guide", "gentle", 2, {"guide"}),
    "Nia": Helper("Nia", "the lantern-bearer", "a lantern-bearer", "calm", 2, {"guide"}),
}

RESPONSES = {
    "rope": Response("rope", 3, 2, "found the rope and tied a safe knot around the token", "reached too quickly and slipped past the token", "found the rope and tied a safe knot around the token", {"safe"}),
    "ladder": Response("ladder", 2, 1, "set up a little ladder and climbed with care", "placed the ladder badly and could not reach", "set up a little ladder and climbed with care", {"safe"}),
    "shout": Response("shout", 1, 0, "called loudly for help", "shouted, but shouting alone could not save the quest", "called loudly for help", {"unsafe"}),
}

GENDERS = ["girl", "boy"]
NAMES = ["Ari", "Lio", "Mira", "Nia", "Tavi", "Sol"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for hid in HELPERS:
                if "column" in QUESTS[qid].tags:
                    combos.append((sid, qid, hid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    helper: str
    response: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = [
    ("What is a column?", "A column is a tall upright pillar that can hold up a roof or stand as a grand marker."),
    ("What does bravery mean?", "Bravery means doing what is right even when you feel nervous. It is not the same as being loud."),
    ("What is parody?", "A parody is a playful imitation of a serious story or song. It copies the shape but adds a funny twist."),
    ("What is a quest?", "A quest is a journey to find something important or to do a hard task."),
    ("Why do heroes use helpers?", "Helpers give good advice, tools, or courage when a task is too hard to do alone."),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-style story for a child that includes the words "parody" and "column" and teaches bravery.',
        f"Tell a small myth where {f['hero'].id} wants to climb a column for a quest, but learns that bravery means careful steps.",
        f'Write a playful heroic story that sounds like an old myth, uses the word "parody", and ends with a recovered quest token.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, setting, quest = f["hero"], f["helper"], f["setting"], f["quest"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {hero.id}, who came to {setting.place} for a quest. {helper.id} helped make the brave choice feel possible."),
        QAItem(question="Why did the hero climb the column?", answer=f"{hero.id} climbed the column to recover {quest.phrase}. That made the quest real instead of just a boast."),
        QAItem(question="What did bravery look like here?", answer=f"Bravery looked like slowing down, choosing the rope, and taking careful steps. The hero proved courage by doing the hard thing safely."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combination does not make a credible mythic quest.)"


ASP_RULES = r"""
valid(S,Q,H) :- setting(S), quest(Q), helper(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, helper=None, response=None, name=None, gender=None, parent=None), random.Random(777)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic parody column quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, helper = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, quest, helper, response, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], HELPERS[params.helper], RESPONSES[params.response], params.name, params.gender, params.parent, params.seed)
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
    StoryParams("mythic_hall", "parody_scroll", "Mira", "rope", "Ari", "boy", "mother"),
    StoryParams("sun_temple", "copper_ring", "Nia", "ladder", "Lio", "boy", "father"),
    StoryParams("moon_court", "bright_banner", "Mira", "rope", "Tavi", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible quest combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
