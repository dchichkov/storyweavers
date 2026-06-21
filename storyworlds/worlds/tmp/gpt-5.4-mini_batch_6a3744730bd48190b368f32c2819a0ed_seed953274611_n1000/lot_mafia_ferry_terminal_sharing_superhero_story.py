#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lot_mafia_ferry_terminal_sharing_superhero_story.py
===================================================================================

A small standalone storyworld built from the seed:
- words: lot, mafia
- setting: ferry terminal
- feature: sharing
- style: superhero story

This world models a child superhero scene at a ferry terminal where a small
problem about having a lot of snacks, a lot of waiting, and a greedy "mafia"
of seagulls turns into a sharing-based resolution.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    lot: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    sharing: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Faction:
    id: str
    label: str
    vibe: str
    greedy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    crowd = world.entities.get("crowd")
    if hero and hero.memes["sharing"] >= THRESHOLD and crowd:
        sig = ("spread", "sharing")
        if sig not in world.fired:
            world.fired.add(sig)
            crowd.meters["calm"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("spread", "social", _r_spread)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid, f in FACTIONS.items():
            for iid, item in ITEMS.items():
                if f.greedy and item.sharing:
                    combos.append((sid, fid, iid))
    return combos


def reasonableness_gate(faction: Faction, item: Item) -> bool:
    return faction.greedy and item.sharing


def explain_rejection(faction: Faction, item: Item) -> str:
    return (
        f"(No story: the {faction.label} only makes sense as a greedy group if "
        f"there is something shareable at risk, and {item.label} is not the right fit.)"
    )


@dataclass
class StoryParams:
    setting: str
    faction: str
    item: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


def setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity, Entity]:
    setting = SETTINGS[params.setting]
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, role="hero",
                            attrs={"setting": setting.id}))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type="mother", role="adult"))
    crowd = world.add(Entity(id="crowd", kind="group", type="people", label="the waiting crowd"))
    item = world.add(Entity(id="item", kind="thing", type="item", label=ITEMS[params.item].label))
    hero.memes["bravery"] = 5.0
    friend.memes["caution"] = 4.0
    crowd.meters["waiting"] = 1.0
    world.facts["setting"] = setting
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["adult"] = adult
    world.facts["crowd"] = crowd
    world.facts["item_cfg"] = ITEMS[params.item]
    world.facts["faction_cfg"] = FACTIONS[params.faction]
    world.facts["response_cfg"] = RESPONSES[params.response]
    return hero, friend, adult, crowd, item


def tell(params: StoryParams) -> World:
    world = World()
    hero, friend, adult, crowd, item = setup(world, params)
    setting = world.facts["setting"]
    faction = world.facts["faction_cfg"]
    response = world.facts["response_cfg"]
    item_cfg = world.facts["item_cfg"]

    world.say(
        f"At the {setting.place}, {hero.id} and {friend.id} stood under the windy roof, "
        f"where there was a lot of people and a lot of humming ferries."
    )
    world.say(
        f"{hero.id} wore a bright cape and felt like a superhero. {setting.detail}"
    )
    world.say(
        f"Near the snack bench, the {faction.label} -- a silly little mafia of "
        f"{faction.vibe} seagulls -- kept eyeing {item_cfg.phrase}."
    )

    world.para()
    hero.memes["sharing"] += 1
    world.say(
        f'{hero.id} lifted {item_cfg.phrase} and said, "We can share the lot of it."'
    )
    world.say(
        f"{friend.id} blinked. {friend.id} had been guarding the bag, but the idea "
        f"of sharing felt kinder than clutching it tight."
    )

    if faction.greedy:
        world.para()
        world.say(
            f"The mafia of seagulls swooped closer, hoping to grab the snacks all at once."
        )
        world.say(
            f'{friend.id} pointed at them and yelled, "Not today!"'
        )

    world.para()
    if response.sense < SENSE_MIN:
        raise StoryError(explain_rejection(faction, item_cfg))

    if response.power < 2:
        world.say(
            f"{adult.label_word.capitalize()} hurried over, but {response.fail.replace('{item}', item_cfg.label)}."
        )
        crowd.meters["worry"] += 1
        world.say(
            "The problem stayed loud for a moment, until the children opened the bag and shared anyway."
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} smiled and {response.text.replace('{item}', item_cfg.label)}."
        )
        crowd.meters["joy"] += 1

    propagate(world, narrate=False)

    world.para()
    world.say(
        f"In the end, the {faction.label} got a cracker each, the crowd got calmer, and "
        f"{hero.id} and {friend.id} watched the ferry lights blink across the water."
    )
    world.say(
        f"Their capes fluttered like flags, and the ferry terminal felt a lot less stormy."
    )

    world.facts.update(
        setting=setting,
        hero=hero,
        friend=friend,
        adult=adult,
        crowd=crowd,
        item_cfg=item_cfg,
        faction_cfg=faction,
        response_cfg=response,
        outcome="shared",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    faction = f["faction_cfg"]
    item = f["item_cfg"]
    return [
        f'Write a superhero story set at a ferry terminal that includes the words "lot" and "mafia" and shows kids choosing to share.',
        f"Tell a child-friendly superhero story where {f['hero'].id} meets a silly {faction.label} at the {setting.place} and shares {item.phrase}.",
        f'Write a story about a lot of waiting, a little mafia of seagulls, and a brave sharing choice at the ferry terminal.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    faction = f["faction_cfg"]
    setting = f["setting"]
    return [
        ("Where does the story happen?",
         f"It happens at the {setting.place}. The windy ferry terminal and the waiting crowd make the scene feel busy."),
        ("Who acts like a superhero?",
         f"{hero.id} acts like a superhero, with a cape and a brave idea. {hero.id} uses sharing like a superpower."),
        ("What is the mafia in the story?",
         f"It is a silly mafia of seagulls, not a real danger. They are greedy and try to snatch the snacks, which makes the sharing choice matter."),
        ("What did the children do with the snacks?",
         f"They shared {item.phrase}. That helped the crowd calm down and made the ferry terminal feel friendlier."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a ferry terminal?",
         "A ferry terminal is a place where people wait for ferries to arrive and leave. It can be busy and windy."),
        ("What does sharing mean?",
         "Sharing means letting other people have some of what you have. It is a kind way to help everyone feel included."),
        ("What is a superhero?",
         "A superhero is a brave helper who tries to make things better. Superheroes often use courage, teamwork, and kindness."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "ferry_terminal": Setting(
        id="ferry_terminal",
        place="the ferry terminal",
        detail="The benches were packed with travelers, and gulls circled the dock lights.",
        lot="lot",
    )
}

ITEMS = {
    "snack_bag": Item(
        id="snack_bag",
        label="snack bag",
        phrase="a snack bag with a lot of crackers",
        sharing=True,
        tags={"lot", "sharing"},
    ),
    "juice_box": Item(
        id="juice_box",
        label="juice box",
        phrase="a juice box and a few extra cups",
        sharing=True,
        tags={"sharing"},
    ),
}

FACTIONS = {
    "seagull_mafia": Faction(
        id="seagull_mafia",
        label="seagull mafia",
        vibe="hungry",
        greedy=True,
        tags={"mafia"},
    )
}

RESPONSES = {
    "share": Response(
        id="share",
        sense=3,
        power=3,
        text="helped them share the snacks with everyone who was waiting",
        fail="almost started to sort the snacks, but there was still too much tugging",
        qa_text="helped the children share the snacks with the waiting crowd",
        tags={"sharing"},
    ),
    "offer_all": Response(
        id="offer_all",
        sense=2,
        power=2,
        text="opened the bag and offered a snack to each person in line",
        fail="opened the bag, but the crowd stayed restless for a bit",
        qa_text="opened the bag and offered a snack to each person in line",
        tags={"sharing"},
    ),
}

HERO_NAMES = ["Ava", "Milo", "Nina", "Leo", "Zoe"]
FRIEND_NAMES = ["Ben", "Mia", "Theo", "Luna", "Max"]


@dataclass
class StoryParams:
    setting: str
    faction: str
    item: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="ferry_terminal", faction="seagull_mafia", item="snack_bag",
                response="share", hero_name="Ava", hero_gender="girl",
                friend_name="Ben", friend_gender="boy", seed=1),
    StoryParams(setting="ferry_terminal", faction="seagull_mafia", item="juice_box",
                response="offer_all", hero_name="Leo", hero_gender="boy",
                friend_name="Mia", friend_gender="girl", seed=2),
]


def valid_response_ids() -> list[str]:
    return [r.id for r in sensible_responses()]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.sharing:
            lines.append(asp.fact("sharing_item", iid))
    for fid, fac in FACTIONS.items():
        lines.append(asp.fact("faction", fid))
        if fac.greedy:
            lines.append(asp.fact("greedy", fid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, F, I) :- setting(S), faction(F), item(I), greedy(F), sharing_item(I).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
outcome(shared) :- chosen_response(R), sensible(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_response", params.response)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) == set(valid_response_ids()):
        print(f"OK: sensible responses match ({valid_response_ids()}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses")
    sample = generate(CURATED[0])
    if not sample.story:
        rc = 1
        print("MISMATCH: sample story empty")
    elif "mafia" not in sample.story or "lot" not in sample.story:
        rc = 1
        print("MISMATCH: story missing seed words")
    else:
        print("OK: smoke test story generated.")
    if asp_outcome(CURATED[0]) != "shared":
        rc = 1
        print("MISMATCH: ASP outcome")
    else:
        print("OK: ASP outcome matches.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero ferry terminal sharing storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--faction", choices=FACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    faction = args.faction or rng.choice(list(FACTIONS))
    item = args.item or rng.choice(list(ITEMS))
    if args.faction and args.item:
        if not reasonableness_gate(FACTIONS[args.faction], ITEMS[args.item]):
            raise StoryError(explain_rejection(FACTIONS[args.faction], ITEMS[args.item]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.faction is None or c[1] == args.faction)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, faction, item = rng.choice(sorted(combos))
    response = args.response or rng.choice(valid_response_ids())
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(setting=setting, faction=faction, item=item, response=response,
                       hero_name=hero_name, hero_gender=hero_gender,
                       friend_name=friend_name, friend_gender=friend_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.faction not in FACTIONS:
        raise StoryError("Unknown faction.")
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, f, i in asp_valid_combos():
            print(f"  {s:15} {f:15} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
