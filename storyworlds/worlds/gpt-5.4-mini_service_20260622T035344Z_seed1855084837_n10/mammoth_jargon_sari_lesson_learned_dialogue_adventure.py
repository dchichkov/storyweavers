#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035344Z_seed1855084837_n10/mammoth_jargon_sari_lesson_learned_dialogue_adventure.py
===============================================================================================================================

A compact storyworld about an adventure at a hill museum, where a child, a guide,
and a family member have to navigate confusing jargon, a giant mammoth exhibit,
and a sari that becomes the key to a safe, thoughtful ending.

The seed words are used directly in the world:
- mammoth
- jargon
- sari

The narrative style is adventure-flavored, with dialogue and a lesson learned.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


def _lazy_asp():
    import asp  # type: ignore
    return asp


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    guide: str
    child_name: str
    child_gender: str
    adult: str
    exhibit: str
    jargon: str
    cloth: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = json.loads(json.dumps({k: _entity_to_dict(v) for k, v in self.entities.items()}))
        clone.entities = {k: _dict_to_entity(v) for k, v in clone.entities.items()}
        clone.facts = json.loads(json.dumps(self.facts))
        clone.history = json.loads(json.dumps(self.history))
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _entity_to_dict(e: Entity) -> dict[str, Any]:
    return {
        "id": e.id, "kind": e.kind, "type": e.type, "label": e.label, "phrase": e.phrase,
        "role": e.role, "traits": list(e.traits), "owner": e.owner, "caretaker": e.caretaker,
        "plural": e.plural, "tags": sorted(e.tags), "attrs": e.attrs,
        "meters": dict(e.meters), "memes": dict(e.memes),
    }


def _dict_to_entity(d: dict[str, Any]) -> Entity:
    e = Entity(
        id=d["id"], kind=d["kind"], type=d["type"], label=d["label"], phrase=d["phrase"],
        role=d["role"], traits=list(d["traits"]), owner=d["owner"], caretaker=d["caretaker"],
        plural=d["plural"], tags=set(d["tags"]), attrs=dict(d["attrs"]),
    )
    e.meters.update(d["meters"])
    e.memes.update(d["memes"])
    return e


@dataclass
class Rule:
    name: str
    apply: Any


def _r_confusion(world: World) -> list[str]:
    out = []
    child = world.get("child")
    guide = world.get("guide")
    exhibit = world.get("exhibit")
    if child.memes["confused"] >= THRESHOLD and guide.memes["explaining"] >= THRESHOLD:
        sig = ("confusion",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.event("confusion")
            out.append(f"{guide.label} noticed {child.label} was still puzzled by the jargon.")
    if exhibit.meters["covered"] >= THRESHOLD and exhibit.memes["calm"] < THRESHOLD:
        sig = ("covered",)
        if sig not in world.fired:
            world.fired.add(sig)
            exhibit.memes["calm"] += 1
            out.append("The old exhibit stayed safe under the cloth.")
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class Setting:
    place: str
    clue: str
    journey: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Exhibit:
    id: str
    label: str
    phrase: str
    size: str
    risk: str
    needs_cover: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "museum": Setting(place="the hill museum", clue="a narrow hallway of maps", journey="climbed the stone steps", afford={"museum"}),
    "archive": Setting(place="the old archive room", clue="a shelf of dusty books", journey="followed a lantern down the corridor", afford={"archive"}),
}

EXHIBITS = {
    "mammoth": Exhibit(id="mammoth", label="mammoth", phrase="the giant mammoth exhibit", size="huge", risk="dust", tags={"mammoth", "adventure"}),
    "statue": Exhibit(id="statue", label="statue", phrase="the cracked stone statue", size="tall", risk="dust", tags={"stone"}),
}

TOOLS = {
    "sari": Tool(id="sari", label="sari", phrase="a bright sari", protects={"dust"}, tags={"sari", "cloth"}),
    "sheet": Tool(id="sheet", label="sheet", phrase="a clean sheet", protects={"dust"}, tags={"cloth"}),
}

GIRL_NAMES = ["Asha", "Nina", "Mira", "Lila", "Anya", "Rina"]
BOY_NAMES = ["Arun", "Kiran", "Dev", "Omar", "Tariq", "Ravi"]
TRAITS = ["curious", "brave", "patient", "quick-thinking", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for exhibit in EXHIBITS:
            for cloth in TOOLS:
                combos.append((place, exhibit, cloth))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a mammoth, jargon, and a sari.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--cloth", choices=TOOLS)
    ap.add_argument("--guide", choices=["guide", "ranger", "curator"])
    ap.add_argument("--adult", choices=["mother", "father", "aunt"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def explain_rejection() -> str:
    return "(No story: this world needs an exhibit that can be covered and a cloth that can cover it.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cloth and args.cloth not in TOOLS:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.exhibit is None or c[1] == args.exhibit)
              and (args.cloth is None or c[2] == args.cloth)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, exhibit, cloth = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["guide", "ranger", "curator"])
    adult = args.adult or rng.choice(["mother", "father", "aunt"])
    return StoryParams(place=place, guide=guide, child_name=name, child_gender=gender, adult=adult, exhibit=exhibit, jargon="jargon", cloth=cloth)


def _build_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.place]
    exhibit_cfg = EXHIBITS[params.exhibit]
    cloth_cfg = TOOLS[params.cloth]

    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child", traits=["little", "curious"]))
    guide = world.add(Entity(id="guide", kind="character", type="woman" if params.guide == "guide" else "man", label=f"the {params.guide}", role="guide"))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult, label=f"the {params.adult}", role="adult"))
    exhibit = world.add(Entity(id="exhibit", kind="thing", type="thing", label=exhibit_cfg.label, phrase=exhibit_cfg.phrase, tags=set(exhibit_cfg.tags)))
    cover = world.add(Entity(id="cover", kind="thing", type="thing", label=cloth_cfg.label, phrase=cloth_cfg.phrase, tags=set(cloth_cfg.tags), owner=child.id))

    world.facts.update(setting=setting, exhibit_cfg=exhibit_cfg, cloth_cfg=cloth_cfg, child=child, guide=guide, adult=adult, exhibit=exhibit, cover=cover)
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    guide.memes["explaining"] += 1
    adult.memes["worry"] += 1
    return world


def tell(world: World) -> None:
    f = world.facts
    setting: Setting = f["setting"]
    child: Entity = f["child"]
    guide: Entity = f["guide"]
    adult: Entity = f["adult"]
    exhibit: Entity = f["exhibit"]
    cover: Entity = f["cover"]

    world.say(f"{child.label} and {guide.label} climbed to {setting.place} for an adventure among old rooms and big wonders.")
    world.say(f"At the doorway, {guide.label} pointed at {setting.clue} and said, “This way.”")

    world.para()
    world.say(f"{child.label} stared at {exhibit.label} and asked, “Why is the {exhibit.label} so huge?”")
    world.say(f"{guide.label} smiled. “That is the jargon part,” {guide.label} said. “Jargon means special words people use when they work here.”")
    child.memes["confused"] += 1
    world.say(f"{child.label} frowned. “So jargon is just words that sound fancy?”")
    world.say(f"“Sometimes,” {adult.label} said, coming closer. “But we can explain it simply.”")
    propagate(world)

    world.para()
    world.say(f"Then a dusty breeze drifted through the room, and the {exhibit.label} looked like it might get smudged.")
    world.say(f"{child.label} lifted {cover.phrase} and asked, “Should I cover it?”")
    world.say(f"{adult.label} nodded. “Yes. A careful adventure keeps the treasure safe.”")
    exhibit.meters["covered"] += 1
    world.event("covering", cloth=cover.label, exhibit=exhibit.label)

    world.para()
    world.say(f"{child.label} spread {cover.phrase} over {exhibit.label} while {guide.label} held the edge.")
    world.say(f"“That was brave,” {guide.label} said. “You listened, asked, and helped.”")
    child.memes["confidence"] += 1
    child.memes["lesson"] += 1
    adult.memes["pride"] += 1
    world.say(f"{child.label} grinned. “Now I know jargon is just a word, and I do not have to feel lost when someone explains it.”")
    world.say(f"Beside the covered mammoth exhibit, the little team stood smiling, and the hall felt safe again.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child named {f["child"].label} that includes the words "mammoth", "jargon", and "sari".',
        f"Tell an adventure about {f['child'].label} at {f['setting'].place} where {f['guide'].label} explains jargon and a sari helps protect a mammoth exhibit.",
        "Write a child-friendly story with dialogue, a problem that gets fixed, and a lesson learned about asking for simple explanations.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guide: Entity = f["guide"]
    adult: Entity = f["adult"]
    exhibit: Entity = f["exhibit"]
    cover: Entity = f["cover"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Why did {child.label} ask about jargon at {setting.place}?",
            answer=f"{child.label} heard {guide.label} use a special work word and wanted to understand it. {guide.label} explained it in a simple way so the adventure could keep going.",
        ),
        QAItem(
            question=f"What did the sari do for the mammoth exhibit?",
            answer=f"{cover.phrase} covered the {exhibit.label} exhibit and helped keep dust off it. That mattered because the hall had a little breeze and the display needed care.",
        ),
        QAItem(
            question=f"How did {child.label} feel after helping with the mammoth?",
            answer=f"{child.label} felt proud and more confident after helping. The child learned that asking questions and doing careful work can turn confusion into a good adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mammoth?",
            answer="A mammoth was a huge elephant-like animal that lived long ago. People often see mammoth bones or models in museums.",
        ),
        QAItem(
            question="What is jargon?",
            answer="Jargon is special language used by a group of people, like workers in a museum or doctors in a clinic. It can sound confusing if you have not learned it yet.",
        ),
        QAItem(
            question="What is a sari?",
            answer="A sari is a long cloth garment worn in many places. It can also be used like a cloth cover when something needs protecting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P, E, C) :- place(P), exhibit(E), cloth(C), coverable(E), protector(C).
"""


def asp_facts() -> str:
    asp = _lazy_asp()
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for e, cfg in EXHIBITS.items():
        lines.append(asp.fact("exhibit", e))
        if cfg.needs_cover:
            lines.append(asp.fact("coverable", e))
    for c, cfg in TOOLS.items():
        lines.append(asp.fact("cloth", c))
        lines.append(asp.fact("protector", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    asp = _lazy_asp()
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid-combos.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, exhibit=None, cloth=None, guide=None, adult=None, name=None, gender=None), random.Random(777)))
        _ = sample.story
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print(f"OK: ASP and Python agree on {len(valid_combos())} combos, and story generation works.")
    return 0


CURATED = [
    StoryParams(place="museum", guide="guide", child_name="Asha", child_gender="girl", adult="mother", exhibit="mammoth", jargon="jargon", cloth="sari", seed=1),
    StoryParams(place="archive", guide="curator", child_name="Arun", child_gender="boy", adult="father", exhibit="statue", jargon="jargon", cloth="sheet", seed=2),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.exhibit not in EXHIBITS or params.cloth not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = _build_world(params)
    tell(world)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
        print("history:", sample.world.history)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
