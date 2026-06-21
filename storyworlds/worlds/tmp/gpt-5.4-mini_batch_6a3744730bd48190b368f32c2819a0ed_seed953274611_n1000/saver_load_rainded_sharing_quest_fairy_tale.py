#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/saver_load_rainded_sharing_quest_fairy_tale.py
===============================================================================

A small fairy-tale storyworld about a brave saver on a quest, a heavy load to
carry, a sharing choice, and a magical rain that "rainded" over the path.

This world keeps the contract used by the Storyweavers repo:
- typed entities with physical meters and emotional memes
- state-driven narration
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in the simulated world
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
SAVER_BRAVE = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class CharacterSpec:
    id: str
    type: str
    role: str
    label: str
    brave: int = 4
    kind: str = "character"


@dataclass
class PlaceSpec:
    id: str
    label: str
    scene: str
    quest_name: str


@dataclass
class LoadSpec:
    id: str
    label: str
    phrase: str
    heavy: bool = True


@dataclass
class WeatherSpec:
    id: str
    label: str
    verb: str
    adds_mud: bool = True


@dataclass
class ShareSpec:
    id: str
    label: str
    text: str
    helps: bool = True


@dataclass
class QuestSpec:
    id: str
    label: str
    goal: str
    reward: str


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mud(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["rainded"] < THRESHOLD:
            continue
        sig = ("mud", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["muddy"] += 1
        e.memes["worry"] += 1
        out.append("__mud__")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    saver = world.get("saver")
    helper = world.get("helper")
    if saver.meters["share"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["load_share"] += 1
    saver.meters["load_share"] += 1
    saver.meters["load"] = max(0.0, saver.meters["load"] - 1)
    helper.meters["load"] = helper.meters["load"] + 1
    saver.memes["relief"] += 1
    helper.memes["joy"] += 1
    out.append("__share__")
    return out


def _r_finish(world: World) -> list[str]:
    out = []
    quest = world.get("quest")
    saver = world.get("saver")
    helper = world.get("helper")
    if quest.meters["done"] >= THRESHOLD:
        return out
    if saver.meters["load"] <= THRESHOLD and helper.meters["load"] > 0:
        sig = ("finish",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        quest.meters["done"] = 1
        saver.memes["joy"] += 1
        helper.memes["joy"] += 1
        out.append("__finish__")
    return out


CAUSAL_RULES = [
    Rule("mud", "weather", _r_mud),
    Rule("share", "social", _r_share),
    Rule("finish", "quest", _r_finish),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reason_ok(load: LoadSpec, share: ShareSpec, quest: QuestSpec) -> bool:
    return load.heavy and share.helps and bool(quest.goal)


def maybe_share(world: World, saver: Entity, helper: Entity, share: ShareSpec) -> None:
    saver.meters["share"] += 1
    saver.memes["hope"] += 1
    world.say(
        f"{saver.id} saw how the path bent under the load and whispered that "
        f"sharing would make the quest kinder."
    )
    world.say(
        f'"{share.text}," said {helper.id}, and the two friends took up the load together.'
    )


def start(world: World, place: PlaceSpec, saver: Entity, helper: Entity, load: LoadSpec, quest: QuestSpec) -> None:
    saver.memes["bravery"] = SAVER_BRAVE
    helper.memes["care"] += 1
    saver.meters["load"] = 2
    helper.meters["load"] = 0
    world.say(
        f"Once in {place.label}, {saver.id} the saver set out on a fairy-tale quest. "
        f"{place.scene}"
    )
    world.say(
        f"{saver.id} carried {load.phrase}, for the quest was to bring it to {quest.goal}."
    )


def trouble(world: World, weather: WeatherSpec, saver: Entity, helper: Entity) -> None:
    world.say(
        f"Before long, the sky {weather.verb}, and the little road turned silver and slick."
    )
    if weather.adds_mud:
        saver.meters["rainded"] += 1
        helper.meters["rainded"] += 1
        propagate(world, narrate=False)
        world.say(
            f"It {weather.label} so hard that the path rainded down the leaves and the boots."
        )


def choice(world: World, saver: Entity, helper: Entity, share: ShareSpec, quest: QuestSpec) -> None:
    if saver.meters["load"] > THRESHOLD:
        maybe_share(world, saver, helper, share)
        world.para()
        world.say(
            f"At once, the load grew lighter in {saver.pronoun('possessive')} arms, "
            f"and {helper.id} smiled as if a lantern had been lit inside the dark wood."
        )
        saver.meters["load"] -= 1
        helper.meters["load"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Together they walked on until the quest was done and {quest.reward} was theirs."
        )
    else:
        world.say(
            f"{saver.id} did not need to share the load, and the quest went on in a steady way."
        )
        world.say(
            f"By sunset, {saver.id} reached {quest.goal} with {quest.reward} held high."
        )


def tell(place: PlaceSpec, load: LoadSpec, weather: WeatherSpec, share: ShareSpec, quest: QuestSpec,
         saver_name: str = "Mina", saver_type: str = "girl",
         helper_name: str = "Pip", helper_type: str = "fox") -> World:
    world = World()
    saver = world.add(Entity(id=saver_name, kind="character", type=saver_type, role="saver", label="the saver"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label="the helper"))
    world.add(Entity(id="quest", kind="thing", type="quest", label=quest.label))
    world.add(Entity(id="load", kind="thing", type="load", label=load.label))
    start(world, place, saver, helper, load, quest)
    world.para()
    trouble(world, weather, saver, helper)
    world.para()
    choice(world, saver, helper, share, quest)
    world.facts.update(place=place, load=load, weather=weather, share=share, quest=quest, saver=saver, helper=helper)
    return world


PLACES = {
    "forest": PlaceSpec(id="forest", label="the emerald forest", scene="Birdsong drifted through the trees, and a moonlit path wound toward the old bridge.", quest_name="moon bridge"),
    "hill": PlaceSpec(id="hill", label="the high hill", scene="Wind combed the grass, and a stone trail climbed toward a tiny castle on the clouds.", quest_name="cloud castle"),
    "river": PlaceSpec(id="river", label="the singing river", scene="Willows leaned over the water, and a winding path led to the little ferry house.", quest_name="ferry house"),
}

LOADS = {
    "bundle": LoadSpec(id="bundle", label="bundle", phrase="a bundle of golden apples"),
    "books": LoadSpec(id="books", label="books", phrase="a stack of story books"),
    "crates": LoadSpec(id="crates", label="crates", phrase="two small crates of bread"),
}

WEATHERS = {
    "raindrift": WeatherSpec(id="raindrift", label="rainded", verb="rainded"),
    "drizzle": WeatherSpec(id="drizzle", label="drizzled", verb="drizzled"),
}

SHARES = {
    "split": ShareSpec(id="split", label="split the load", text="Let's split the load so the quest can continue"),
    "carry": ShareSpec(id="carry", label="carry together", text="I'll carry one end, and you carry the other"),
}

QUESTS = {
    "gift": QuestSpec(id="gift", label="gift", goal="the queen's table", reward="a silver thank-you ribbon"),
    "bridge": QuestSpec(id="bridge", label="bridge", goal="the little bridge", reward="the bridge bell to ring"),
}

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Rosa", "Elin"]
BOY_NAMES = ["Pip", "Robin", "Otto", "Finn", "Tobin"]


@dataclass
class StoryParams:
    place: str
    load: str
    weather: str
    share: str
    quest: str
    saver_name: str = "Mina"
    saver_type: str = "girl"
    helper_name: str = "Pip"
    helper_type: str = "fox"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for lid in LOADS:
            for wid in WEATHERS:
                for sid in SHARES:
                    for qid in QUESTS:
                        combos.append((pid, lid, wid, sid, qid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a saver, a load, sharing, and a quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              if (args.place is None or c[0] == args.place)
              and (args.load is None or c[1] == args.load)
              and (args.weather is None or c[2] == args.weather)
              and (args.share is None or c[3] == args.share)
              and (args.quest is None or c[4] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, load, weather, share, quest = rng.choice(sorted(combos))
    saver_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    saver_type = "girl" if saver_name in GIRL_NAMES else "boy"
    helper_name = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != saver_name] + ["Pip"])
    helper_type = "fox" if helper_name == "Pip" else ("girl" if helper_name in GIRL_NAMES else "boy")
    return StoryParams(place=place, load=load, weather=weather, share=share, quest=quest,
                       saver_name=saver_name, saver_type=saver_type,
                       helper_name=helper_name, helper_type=helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story with the words "saver", "load", and "rainded".',
        f"Tell a quest story where {f['saver'].id} the saver learns to share the load with {f['helper'].id}.",
        f"Write a gentle story about sharing on a quest, where the weather {f['weather'].verb} and the travelers keep going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    saver = f["saver"]
    helper = f["helper"]
    load = f["load"]
    quest = f["quest"]
    weather = f["weather"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {saver.id}, the saver, who went on a fairy-tale quest with {helper.id}. {saver.id} carried {load.phrase} at the start."
        ),
        QAItem(
            question="Why did the saver share the load?",
            answer=f"{weather.label.capitalize()} made the path slippery and heavy to cross. Sharing the load made it easier to keep going toward {quest.goal}."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The friends reached {quest.goal} together and won {quest.reward}. The load was lighter because they shared it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a load?", "A load is something heavy to carry, like a bundle, books, or crates. A load can feel easier when two friends share it."),
        QAItem("What does it mean to share?", "To share means to divide something or carry it together so no one has to do all the work alone."),
        QAItem("What is a quest?", "A quest is a special journey with a goal to reach. In fairy tales, quests often end with a gift, a prize, or a happy return home."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", load="bundle", weather="raindrift", share="split", quest="gift", saver_name="Mina", saver_type="girl", helper_name="Pip", helper_type="fox"),
    StoryParams(place="hill", load="books", weather="drizzle", share="carry", quest="bridge", saver_name="Robin", saver_type="boy", helper_name="Lina", helper_type="girl"),
    StoryParams(place="river", load="crates", weather="raindrift", share="carry", quest="gift", saver_name="Tessa", saver_type="girl", helper_name="Otto", helper_type="boy"),
]


def generate(params: StoryParams) -> StorySample:
    for key, table in [("place", PLACES), ("load", LOADS), ("weather", WEATHERS), ("share", SHARES), ("quest", QUESTS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        PLACES[params.place],
        LOADS[params.load],
        WEATHERS[params.weather],
        SHARES[params.share],
        QUESTS[params.quest],
        saver_name=params.saver_name,
        saver_type=params.saver_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )
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


ASP_RULES = r"""
share_possible(S) :- share(S), helps(S).
quest_done :- saver(load_light), share_possible(_).
outcome(happy) :- quest_done.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        if l.heavy:
            lines.append(asp.fact("heavy", lid))
    for wid in WEATHERS:
        lines.append(asp.fact("weather", wid))
    for sid, s in SHARES.items():
        lines.append(asp.fact("share", sid))
        if s.helps:
            lines.append(asp.fact("helps", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show share_possible/1."))
    return sorted(set(asp.atoms(model, "share_possible")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"FAILED: generate smoke test crashed: {e}")
        return 1
    if not reason_ok(LOADS["bundle"], SHARES["split"], QUESTS["gift"]):
        print("FAILED: reasonableness gate regression")
        rc = 1
    print(f"OK: smoke test produced {len(sample.story)} characters.")
    return rc


def explain_rejection() -> str:
    return "(No story: this world needs a heavy load and a sharing choice that can really help on the quest.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show share_possible/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("share options:", asp_valid_combos())
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
            params = resolve_params(args, random.Random(seed))
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
