#!/usr/bin/env python3
"""
storyworlds/worlds/lively_sharing_fairy_tale.py
==============================================

A small fairy-tale storyworld about lively sharing in a village near the woods.

Seed inspiration:
- Write a fairy tale style story
- Include the word "lively"
- Center on sharing

This world models a short, child-facing tale where a lively child notices a
neighbor in need, decides whether to share a precious good, and ends with a
physical image that proves the change: split bread, half a cloak, shared jam,
or a lantern passed from one hand to another.

The simulation tracks typed entities with physical meters and emotional memes,
drives prose from world state, and includes a small ASP twin for the valid
combination gate.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    outdoors: bool = True
    mood: str = ""


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    sharing_verb: str
    half_phrase: str
    ending_image: str
    need_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    need_phrase: str
    at_risk: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    offer: str
    end_clause: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "meadow": Setting(id="meadow", place="the meadow by the willow", outdoors=True, mood="golden"),
    "cottage": Setting(id="cottage", place="the cottage kitchen", outdoors=False, mood="warm"),
    "market": Setting(id="market", place="the village market", outdoors=True, mood="busy"),
    "orchard": Setting(id="orchard", place="the orchard gate", outdoors=True, mood="sweet"),
}

GIFTS = {
    "bread": Gift(
        id="bread",
        label="a round loaf of bread",
        phrase="a round loaf of bread wrapped in linen",
        sharing_verb="break the bread",
        half_phrase="half the loaf",
        ending_image="a loaf split into two warm halves",
        need_word="hunger",
        tags={"bread", "food", "sharing"},
    ),
    "berries": Gift(
        id="berries",
        label="a basket of berries",
        phrase="a basket of berries picked at dawn",
        sharing_verb="share the berries",
        half_phrase="half the berries",
        ending_image="two little bowls of berries",
        need_word="thirst",
        tags={"berries", "food", "sharing"},
    ),
    "cloak": Gift(
        id="cloak",
        label="a bright blue cloak",
        phrase="a bright blue cloak with a silver clasp",
        sharing_verb="share the cloak",
        half_phrase="the cloak draped over both shoulders",
        ending_image="one blue cloak held around two small shoulders",
        need_word="cold",
        tags={"cloak", "warmth", "sharing"},
    ),
    "lantern": Gift(
        id="lantern",
        label="a lantern with a honey glow",
        phrase="a lantern with a honey glow",
        sharing_verb="share the lantern light",
        half_phrase="the lantern light between them",
        ending_image="one lantern glowing between two faces",
        need_word="darkness",
        tags={"lantern", "light", "sharing"},
    ),
}

NEEDS = {
    "hungry": Need(id="hungry", label="hungry", need_phrase="a hungry belly", at_risk="food", solved_by="bread", tags={"food"}),
    "thirsty": Need(id="thirsty", label="thirsty", need_phrase="a dry throat", at_risk="food", solved_by="berries", tags={"food"}),
    "cold": Need(id="cold", label="cold", need_phrase="shivery hands", at_risk="warmth", solved_by="cloak", tags={"warmth"}),
    "dark": Need(id="dark", label="dark", need_phrase="the dim path home", at_risk="light", solved_by="lantern", tags={"light"}),
}

HELPERS = {
    "bird": Helper(id="bird", label="a little sparrow", offer="chirped from the eaves", end_clause="the sparrow fluttered happily above them", tags={"bird"}),
    "grandmother": Helper(id="grandmother", label="the grandmother", offer="smiled with wise eyes", end_clause="the grandmother nodded from her stool", tags={"grandmother"}),
    "fountain": Helper(id="fountain", label="the village fountain", offer="splashed gently nearby", end_clause="the fountain sparkled beside them", tags={"fountain"}),
}

GIRL_NAMES = ["Lina", "Mira", "Sera", "Nora", "Elsa", "Lily"]
BOY_NAMES = ["Owen", "Theo", "Pip", "Bram", "Eli", "Finn"]
TRAITS = ["lively", "cheerful", "curious", "kind", "brave", "gentle"]


@dataclass
class StoryParams:
    setting: str = "meadow"
    gift: str = "bread"
    need: str = "hungry"
    helper: str = "bird"
    child_name: str = "Lina"
    child_gender: str = "girl"
    visitor_name: str = "Milo"
    visitor_gender: str = "boy"
    parent_name: str = "the mother"
    trait: str = "lively"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    rows = []
    for sid, setting in SETTINGS.items():
        for gid, gift in GIFTS.items():
            for nid, need in NEEDS.items():
                if gift.id == need.solved_by:
                    rows.append((sid, gid, nid))
    return rows


def explain_invalid(setting: Setting, gift: Gift, need: Need) -> str:
    return (
        f"(No story: {gift.label} does not fit the need '{need.label}' in a way "
        f"that makes a fair sharing tale. Choose the matching pair instead.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.gift and args.need:
        if (args.setting, args.gift, args.need) not in valid_combos():
            raise StoryError(explain_invalid(SETTINGS[args.setting], GIFTS[args.gift], NEEDS[args.need]))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.gift is None or c[1] == args.gift)
        and (args.need is None or c[2] == args.need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, gift, need = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    visitor_gender = args.visitor_gender or rng.choice(["girl", "boy"])
    visitor_name = args.visitor_name or rng.choice(GIRL_NAMES if visitor_gender == "girl" else BOY_NAMES)
    parent_name = args.parent or rng.choice(["the mother", "the father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, gift=gift, need=need, helper=helper,
                       child_name=child_name, child_gender=child_gender,
                       visitor_name=visitor_name, visitor_gender=visitor_gender,
                       parent_name=parent_name, trait=trait)


def _init_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name,
                             role="giver", attrs={}, meters={"joy": 0.0, "share": 0.0}, memes={"joy": 0.0, "care": 0.0}))
    visitor = world.add(Entity(id="visitor", kind="character", type=params.visitor_gender, label=params.visitor_name,
                               role="receiver", attrs={}, meters={"need": 0.0}, memes={"hope": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type="woman" if "mother" in params.parent_name else "man",
                              label=params.parent_name, role="guide", attrs={}, meters={}, memes={"pride": 0.0}))
    gift = world.add(Entity(id="gift", label=GIFTS[params.gift].label, phrase=GIFTS[params.gift].phrase,
                            attrs={"gift_id": params.gift}, meters={"whole": 1.0}, memes={"value": 1.0}))
    helper = world.add(Entity(id="helper", label=HELPERS[params.helper].label, attrs={}, meters={}, memes={"warmth": 0.0}))
    world.facts = {
        "child": child, "visitor": visitor, "parent": parent, "gift": gift, "helper": helper,
        "setting": setting, "gift_cfg": GIFTS[params.gift], "need_cfg": NEEDS[params.need], "helper_cfg": HELPERS[params.helper],
        "shared": False, "resolved": False, "asked": False,
    }
    return world


def _do_share(world: World) -> None:
    child = world.facts["child"]
    visitor = world.facts["visitor"]
    gift_cfg = world.facts["gift_cfg"]
    need_cfg = world.facts["need_cfg"]
    gift = world.facts["gift"]
    sig = ("share", gift_cfg.id, need_cfg.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.meters["share"] = 1.0
    child.memes["joy"] += 1.0
    visitor.memes["hope"] += 1.0
    gift.meters["whole"] = 0.0
    gift.meters["shared"] = 1.0
    world.facts["shared"] = True
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = _init_world(params)
    child = world.facts["child"]
    visitor = world.facts["visitor"]
    parent = world.facts["parent"]
    helper = world.facts["helper"]
    gift_cfg = world.facts["gift_cfg"]
    need_cfg = world.facts["need_cfg"]

    world.say(f"In {world.setting.place}, {child.label} was a {params.trait} child with a bright smile.")
    world.say(f"One day, {child.label} carried {gift_cfg.phrase}, and the day felt especially lively.")
    world.say(f"Near by, {visitor.label} came with {need_cfg.need_phrase}, and {helper.label} {helper.attrs.get('offer', HELPERS[params.helper].offer)}.")
    world.para()
    world.say(f"{visitor.label} looked at {gift_cfg.label} and sighed, for {visitor.label} had {need_cfg.need_phrase}.")
    world.say(f"{child.label} wanted to keep the gift, but {parent.label} said, 'A kind heart grows bigger when it shares.'")
    world.say(f"Then {helper.label} reminded {child.label} that {gift_cfg.label} could help more than one friend.")

    world.para()
    _do_share(world)
    world.say(f"{child.label} smiled and chose to {gift_cfg.sharing_verb}.")
    world.say(f"{child.label} gave {gift_cfg.half_phrase} to {visitor.label}, and both faces softened at once.")
    world.say(f"{helper.end_clause}.")
    world.say(f"In the end, there was {gift_cfg.ending_image}, and the whole place looked warm with kindness.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    visitor = f["visitor"]
    gift_cfg = f["gift_cfg"]
    need_cfg = f["need_cfg"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old about {child.label} sharing {gift_cfg.label} when {visitor.label} has {need_cfg.need_phrase}. Include the word "lively".',
        f"Tell a gentle fairy tale where a {child.label} is lively, sees {visitor.label} in need, and learns to share {gift_cfg.label}.",
        f'Write a short fairy tale about kindness and sharing that ends with {gift_cfg.ending_image}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    visitor = f["visitor"]
    parent = f["parent"]
    gift_cfg = f["gift_cfg"]
    need_cfg = f["need_cfg"]
    helper_cfg = f["helper_cfg"]
    return [
        QAItem(
            question=f"Who is the story about in the fairy tale with {child.label} and {gift_cfg.label}?",
            answer=f"It is about {child.label}, who is a lively child in {world.setting.place}. {parent.label} and {visitor.label} matter too, because they help the sharing story happen.",
        ),
        QAItem(
            question=f"Why did {child.label} decide to share {gift_cfg.label}?",
            answer=f"{visitor.label} had {need_cfg.need_phrase}, so {child.label} saw a chance to help. The child chose kindness, and that made the gift useful to both children.",
        ),
        QAItem(
            question=f"What did {child.label} do with {gift_cfg.label} at the end?",
            answer=f"{child.label} shared it and gave {gift_cfg.half_phrase} to {visitor.label}. That is why the ending shows {gift_cfg.ending_image}.",
        ),
        QAItem(
            question=f"How did {helper_cfg.label} help the sharing happen?",
            answer=f"{helper_cfg.label} offered a gentle reminder and made the choice feel brave instead of hard. That helped {child.label} do the kind thing and share.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    gift_cfg = f["gift_cfg"]
    need_cfg = f["need_cfg"]
    tags = set(gift_cfg.tags) | set(need_cfg.tags)
    out = []
    if "sharing" in tags:
        out.append(QAItem("What is sharing?", "Sharing means giving part of what you have so someone else can use it too. It can make two children feel happy together."))
    if "food" in tags:
        out.append(QAItem("Why do people share food?", "People share food so everyone can have enough to eat. It is a kind way to help someone who is hungry or thirsty."))
    if "warmth" in tags:
        out.append(QAItem("Why does a cloak help on a cold day?", "A cloak keeps warm air close to your body, so it helps you feel less chilly."))
    if "light" in tags:
        out.append(QAItem("What does a lantern do?", "A lantern gives off light so people can see in the dark."))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind:9}) label={e.label!r} meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, N) :- setting(S), gift(G), need(N), matches(G, N).
matches(bread, hungry).
matches(berries, thirsty).
matches(cloak, cold).
matches(lantern, dark).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP combo gates.")
        print("only in python:", sorted(py - cl))
        print("only in asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, gift=None, need=None, helper=None,
                                                            child_name=None, child_gender=None,
                                                            visitor_name=None, visitor_gender=None,
                                                            parent=None, seed=None), random.Random(777)))
        assert sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: ASP matches Python and generation smoke test passed ({len(py)} combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about lively sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--visitor-name")
    ap.add_argument("--visitor-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["the mother", "the father"])
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.gift not in GIFTS or params.need not in NEEDS:
        raise StoryError("Unknown gift or need.")
    if (params.setting, params.gift, params.need) not in valid_combos():
        raise StoryError(explain_invalid(SETTINGS[params.setting], GIFTS[params.gift], NEEDS[params.need]))
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
    StoryParams(setting="meadow", gift="bread", need="hungry", helper="bird", child_name="Lina", child_gender="girl", visitor_name="Owen", visitor_gender="boy", parent_name="the mother", trait="lively"),
    StoryParams(setting="orchard", gift="berries", need="thirsty", helper="grandmother", child_name="Mira", child_gender="girl", visitor_name="Pip", visitor_gender="boy", parent_name="the father", trait="lively"),
    StoryParams(setting="cottage", gift="cloak", need="cold", helper="fountain", child_name="Finn", child_gender="boy", visitor_name="Sera", visitor_gender="girl", parent_name="the mother", trait="lively"),
    StoryParams(setting="market", gift="lantern", need="dark", helper="bird", child_name="Nora", child_gender="girl", visitor_name="Bram", visitor_gender="boy", parent_name="the father", trait="lively"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.gift is None or c[1] == args.gift)
        and (args.need is None or c[2] == args.need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, gift, need = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        gift=gift,
        need=need,
        helper=args.helper or rng.choice(sorted(HELPERS)),
        child_name=args.child_name or rng.choice(GIRL_NAMES if (args.child_gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        visitor_name=args.visitor_name or rng.choice(GIRL_NAMES if (args.visitor_gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES),
        visitor_gender=args.visitor_gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["the mother", "the father"]),
        trait=rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
