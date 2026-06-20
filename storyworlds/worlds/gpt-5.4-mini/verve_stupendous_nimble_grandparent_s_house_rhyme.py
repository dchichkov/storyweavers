#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/verve_stupendous_nimble_grandparent_s_house_rhyme.py
===================================================================================

A tiny storyworld for a nursery-rhyme style tale set in a grandparent's house.

Premise
-------
A child visits Grandparent's house with a small, cheerful plan for play.
They want to make a rhyme and share a prized treat or toy with a sibling/cousin.
The first attempt is a bit clumsy, then a nimble helper notices a better way:
share the item, keep the rhythm, and turn the moment into a bright little rhyme.

This world keeps the story small and concrete:
- typed entities with physical meters and emotional memes,
- a state-driven narrative with turn and resolution,
- a reasonableness gate,
- a Python gate plus inline ASP twin,
- prompts, story-grounded Q&A, and world-knowledge Q&A.

The story text stays child-facing, with a nursery-rhyme cadence and a complete
ending image showing what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



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
    cozy_detail: str
    rhyme_line: str
    sharing_spot: str

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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    shareable: bool = True
    small: bool = True
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
class Action:
    id: str
    verb: str
    rhythm: str
    stumble: str
    fix: str
    sense: int
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if child.meters["jostle"] >= THRESHOLD and item.meters["held"] < THRESHOLD:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["scattered"] += 1
            child.memes["embarrassed"] += 1
            out.append("The little share went scatter and stray.")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    child = world.get("child")
    if helper.memes["kindness"] >= THRESHOLD and helper.meters["helped"] < THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.meters["helped"] += 1
            child.memes["calm"] += 1
            out.append("A kinder plan came bright that day.")
    return out


CAUSAL_RULES = [
    Rule("spill", "physical", _r_spill),
    Rule("soften", "social", _r_soften),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid, act in ACTIONS.items():
            for iid, item in ITEMS.items():
                if act.id == "share" and item.shareable:
                    combos.append((sid, aid, iid))
                elif act.id == "rhyme" and item.small:
                    combos.append((sid, aid, iid))
    return combos


def predict(world: World, action: Action) -> dict:
    sim = world.copy()
    child = sim.get("child")
    item = sim.get("item")
    if action.id == "share":
        child.meters["jostle"] += 1
        item.meters["held"] += 1
    else:
        child.meters["rhymed"] += 1
    propagate(sim, narrate=False)
    return {
        "scattered": item.meters["scattered"] >= THRESHOLD,
        "calm": child.memes["calm"] >= THRESHOLD,
    }


def _do_action(world: World, action: Action) -> None:
    child = world.get("child")
    item = world.get("item")
    if action.id == "share":
        child.meters["jostle"] += 1
        item.meters["held"] += 1
        propagate(world, narrate=False)
    else:
        child.meters["rhymed"] += 1
        child.memes["joy"] += 1
        propagate(world, narrate=False)


def tell(setting: Setting, action: Action, item: Item,
         child_name: str = "Nina", child_gender: str = "girl",
         helper_name: str = "Milo", helper_gender: str = "boy",
         grandparent_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_gender,
                             label=child_name, role="child"))
    helper = world.add(Entity("helper", kind="character", type=helper_gender,
                              label=helper_name, role="helper"))
    grandparent = world.add(Entity("grandparent", kind="character", type=grandparent_type,
                                   label="Grandparent", role="grandparent"))
    share_item = world.add(Entity("item", kind="thing", type=item.type, label=item.label))
    child.memes["verve"] = 1.0
    helper.memes["kindness"] = 1.0

    world.say(
        f"In Grandparent's house, where the kettle sang and the window shone, "
        f"{child_name} came in with verve and a grin. {setting.cozy_detail}"
    )
    world.say(
        f"{child_name} wanted to {action.verb} and make a rhyme as light as a kite. "
        f"{setting.rhyme_line}"
    )
    world.para()
    child.meters["rhymed"] += 1
    world.say(
        f"But when {child_name} tried to {action.verb}, the little plan went wobbly and thin. "
        f"{action.stumble}"
    )
    if action.id == "share":
        world.say(
            f"{helper_name} was nimble and quick to see the thing that could help the scene. "
            f'"Let us share it, fair and square," {helper_name} said, "and keep it between."'
        )
        _do_action(world, action)
        world.para()
        world.say(
            f"{grandparent.label_word.capitalize()} smiled by the table and clapped in time. "
            f"{action.fix} Then {child_name} and {helper_name} shared the {item.label}, "
            f"and the rhyme grew fine."
        )
        world.say(
            f"They sang, 'One for you and one for me, in Grandparent's house we share with glee.' "
            f"The {item.label} stayed safe, and the room felt bright."
        )
    else:
        world.say(
            f"{helper_name} was nimble and bright, and nudged the beat with a rhyme. "
            f"{action.fix}"
        )
        _do_action(world, action)
        world.para()
        world.say(
            f"{child_name} finished the rhyme with a merry bow, and the {item.label} "
            f"sat snug by the lamp. The day stayed warm and right."
        )

    world.facts.update(
        child=child,
        helper=helper,
        grandparent=grandparent,
        setting=setting,
        action=action,
        item=share_item,
        outcome="shared" if action.id == "share" else "rhyme",
    )
    return world


SETTINGS = {
    "grandparents_house": Setting(
        "grandparents_house",
        "Grandparent's house",
        "A quilt lay over the sofa, and a blue tea cup waited on the sill.",
        "With a tap and a clap and a tippy-toe line,",
        "The carpet was soft for little feet to roam.",
    ),
    "kitchen": Setting(
        "kitchen",
        "Grandparent's kitchen",
        "A pie cooled by the window, and spoons winked in a row.",
        "With a pat and a chat and a sing-song tune,",
        "The floor had a shine like a moonlit spoon.",
    ),
    "porch": Setting(
        "porch",
        "Grandparent's porch",
        "A rocking chair creaked, and a plant waved green hello.",
        "With a twirl and a whirl and a humming note,",
        "The boards made music under a little coat.",
    ),
}

ITEMS = {
    "cookies": Item("cookies", "cookies", "a plate of cookies", "snack", tags={"sharing"}),
    "berries": Item("berries", "berries", "a bowl of berries", "snack", tags={"sharing"}),
    "buttons": Item("buttons", "buttons", "a jar of shiny buttons", "toy", tags={"sharing"}),
    "ribbon": Item("ribbon", "ribbon", "a ribbon for dress-up", "toy", tags={"sharing"}),
}

ACTIONS = {
    "share": Action("share", "share the treat", "sharing the treat", "the plate wobbled and nearly tipped", "So they each took a little and passed it on.", 3, tags={"sharing"}),
    "rhyme": Action("rhyme", "make a rhyme", "making a rhyme", "the words came out crooked and shy", "So they tapped the beat and tried again.", 2, tags={"rhyme"}),
}

NAMES_GIRL = ["Nina", "Lily", "Maya", "Ruby", "Tessa", "Poppy"]
NAMES_BOY = ["Milo", "Eli", "Finn", "Owen", "Theo", "Noah"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    action: str
    item: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    grandparent_type: str
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


KNOWLEDGE = {
    "sharing": [
        ("What is sharing?",
         "Sharing is when two or more people each get a turn or a piece of something. It helps everyone feel included."),
        ("Why is sharing nice?",
         "Sharing is nice because it helps friends and family be kind to one another. It can make play feel fair and happy."),
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is when words sound alike at the end, like cat and hat. Rhymes can make a song or story feel bouncy."),
        ("Why do people clap to a rhyme?",
         "Clapping helps keep the beat steady. The beat makes the rhyme easier to say together."),
    ],
    "grandparents_house": [
        ("What is a grandparent's house?",
         "A grandparent's house is where grandma or grandpa lives and welcomes family. It often feels cozy and full of special things."),
    ],
}
KNOWLEDGE_ORDER = ["sharing", "rhyme", "grandparents_house"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story set in Grandparent\'s house that uses the words "verve", "stupendous", and "nimble".',
        f"Tell a cozy story where {f['child'].label} has verve, {f['helper'].label} is nimble, and they share {f['item'].phrase} in Grandparent's house.",
        f"Write a short rhyme about sharing in Grandparent's house, with a bright ending image and a careful little turn.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    gp = f["grandparent"]
    act = f["action"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.label}, {helper.label}, and {gp.label_word}. They spend the story in Grandparent's house, where the air feels cozy and kind."),
        ("What did the child want to do?",
         f"{child.label} wanted to {act.verb}. That was the first idea, but it needed a better rhythm before it could feel stupendous."),
        ("How did the helper help?",
         f"{helper.label} was nimble and noticed the little wobble. {helper.label} suggested a shared plan, so the moment could turn happy instead of clumsy."),
    ]
    if f.get("outcome") == "shared":
        qa.append((
            "How did they finish the problem?",
            f"They shared {item.phrase} and kept the rhyme going together. The child felt calm again, and the ending showed that the treat stayed neat and the fun stayed bright."
        ))
        qa.append((
            "What changed by the end?",
            f"At the end, {child.label} and {helper.label} were sharing kindly instead of jostling. Grandparent's house felt warm, and the little rhyme sounded stupendous."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with a finished rhyme and a snug, happy room. The child's joy grew, and the words of the song carried the scene home."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["action"].tags) | set(world.facts["item"].tags)
    tags.add("grandparents_house")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def sensible_items() -> list[Item]:
    return [i for i in ITEMS.values() if i.shareable and i.small]


def explain_rejection(action: Action, item: Item) -> str:
    if action.sense < SENSE_MIN:
        return f"(No story: action '{action.id}' is too weak to carry the rhyme.)"
    if not item.shareable:
        return f"(No story: {item.label} is not a fair thing to share.)"
    return "(No story: this combination does not make a reasonable little tale.)"


def outcome_of(params: StoryParams) -> str:
    return "shared" if params.action == "share" else "rhyme"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld in Grandparent's house.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--grandparent", choices=["grandmother", "grandfather"])
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


def valid_story_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid in ACTIONS:
            for iid in ITEMS:
                if aid == "share" and ITEMS[iid].shareable:
                    combos.append((sid, aid, iid))
                if aid == "rhyme" and ITEMS[iid].small:
                    combos.append((sid, aid, iid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.item:
        if args.action == "share" and not ITEMS[args.item].shareable:
            raise StoryError(explain_rejection(ACTIONS[args.action], ITEMS[args.item]))
    combos = [c for c in valid_story_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, item = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice([n for n in (NAMES_BOY if helper_gender == "boy" else NAMES_GIRL) if n != child_name])
    grandparent = args.grandparent or rng.choice(["grandmother", "grandfather"])
    return StoryParams(setting, action, item, child_name, child_gender, helper_name, helper_gender, grandparent)


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    item = ITEMS[params.item]
    return tell(setting, action, item, params.child_name, params.child_gender,
                params.helper_name, params.helper_gender, params.grandparent)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
shareable(Item) :- item(Item), share_ok(Item).
rhymable(Item) :- item(Item), small(Item).
valid(Set, Act, Item) :- setting(Set), action(Act), item(Item), shareable(Item), act_share(Act).
valid(Set, Act, Item) :- setting(Set), action(Act), item(Item), rhymable(Item), act_rhyme(Act).

outcome(shared) :- chosen_action(share).
outcome(rhyme) :- chosen_action(rhyme).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if aid == "share":
            lines.append(asp.fact("act_share", aid))
        if aid == "rhyme":
            lines.append(asp.fact("act_rhyme", aid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shareable:
            lines.append(asp.fact("share_ok", iid))
        if item.small:
            lines.append(asp.fact("small", iid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_action", params.action)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_story_combos()):
        print("MISMATCH in ASP combos.")
        rc = 1
    else:
        print(f"OK: ASP matches valid_story_combos() ({len(valid_story_combos())} combos).")
    samples = [resolve_params(argparse.Namespace(
        setting=None, action=None, item=None, child_name=None, child_gender=None,
        helper_name=None, helper_gender=None, grandparent=None), random.Random(i))
        for i in range(5)]
    if any(asp_outcome(p) != outcome_of(p) for p in samples):
        print("MISMATCH in ASP outcomes.")
        rc = 1
    else:
        print("OK: ASP outcomes match Python.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams("grandparents_house", "share", "cookies", "Nina", "girl", "Milo", "boy", "grandmother"),
    StoryParams("grandparents_house", "rhyme", "buttons", "Leo", "boy", "Maya", "girl", "grandfather"),
    StoryParams("kitchen", "share", "berries", "Ruby", "girl", "Finn", "boy", "grandmother"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} in {SETTINGS[p.setting].place} ({p.action}, {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
