#!/usr/bin/env python3
"""
storyworlds/worlds/definite_freckle_rob_cautionary_myth.py
==========================================================

A small mythic, cautionary story world built from the seed words
"definite", "freckle", and "rob".

Premise:
- A young climber named Rob, nicknamed Freckle, wants a sacred prize.
- An elder gives a definite warning about a dangerous shortcut.
- The child either listens and succeeds, or ignores the warning and suffers.
- The story is resolved through a concrete change in world state, not a frozen
  prose template.

This world is deliberately compact: it supports only a few strong, plausible
mythic variants, all of them cautionary.
"""

from __future__ import annotations

import argparse
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("risk", 0.0)
        self.meters.setdefault("loss", 0.0)
        self.meters.setdefault("gain", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("pride", 0.0)
        self.memes.setdefault("warning", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    path: str
    danger: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Guide:
    id: str
    label: str
    warning: str
    safe: str
    tail: str
    lesson: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _say_join(*parts: str) -> str:
    return " ".join(p for p in parts if p)


def _is_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def _safe_guide(quest: Quest, prize: Prize) -> Optional[Guide]:
    for guide in GUIDES:
        if guide.id == "none":
            continue
        if quest.id in guide.safe and prize.region in guide.safe:
            return guide
    return None


def _apply_risk(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    if hero.memes["warning"] < THRESHOLD:
        hero.meters["risk"] += 1.0
    if quest.id == "river" and hero.memes["warning"] < THRESHOLD:
        prize.meters["loss"] += 1.0
        hero.memes["fear"] += 1.0


def _propagate(world: World) -> None:
    for ent in world.entities.values():
        if ent.meters["loss"] >= THRESHOLD:
            ent.memes["fear"] += 1.0


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str, guide: Guide) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "freckled", "bold"],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type="woman",
        label=guide.label,
        traits=["old", "steady"],
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=elder.id,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["hope"] += 1.0
    hero.memes["pride"] += 1.0

    world.say(
        f"In the old days, when stones still remembered the first rain, there lived "
        f"a little {hero.type} named {hero.id}, and folk called {hero.id} Freckle "
        f"because {hero.pronoun('possessive')} face carried one bright freckle like a dropped star."
    )
    world.say(
        f"{hero.id} longed for {prize.phrase}, for {setting.place} had taught every child that a true gift must be won by patience."
    )
    world.say(
        f"At dusk, {hero.id} met {elder.label}, who spoke a {guide.warning} warning: "
        f'"Take the {setting.path}; the other way is {setting.danger}."'
    )

    world.para()
    world.say(
        f"But {hero.id} looked toward the shorter way by the {setting.danger} and felt {quest.keyword} in {hero.pronoun('possessive')} chest like a drum."
    )
    hero.memes["warning"] += 0.0
    if quest.id == "river":
        world.say(
            f"{hero.id} wished to {quest.verb}, though the water below turned and flashed like a knife."
        )
    elif quest.id == "cave":
        world.say(
            f"{hero.id} wished to {quest.verb}, though the cave mouth breathed cold and old as winter."
        )
    else:
        world.say(
            f"{hero.id} wished to {quest.verb}, though the night road had no lantern and no sign."
        )

    world.say(
        f"Then {hero.id} tried to {quest.rush}, and the warning became heavy as a stone in {hero.pronoun('possessive')} hand."
    )
    hero.memes["warning"] += 1.0
    _apply_risk(world, hero, quest, prize)
    _propagate(world)

    world.para()
    if hero.meters["risk"] >= THRESHOLD and guide.id != "none":
        hero.memes["fear"] += 1.0
        world.say(
            f"{elder.id} stepped near and said, '{guide.safe}'"
        )
        world.say(
            f"{hero.id} bowed {hero.pronoun('possessive')} head at last and chose the {setting.path}."
        )
        hero.memes["hope"] += 1.0
        hero.memes["relief"] += 1.0
        prize.meters["gain"] += 1.0
        hero.memes["warning"] = 0.0
        world.say(
            f"They went together by the {setting.path}, and {guide.tail}."
        )
        world.say(
            f"In the end, {hero.id} returned with {prize.phrase} untouched, and the freckled child learned that a definite warning can be a saving lamp."
        )
    else:
        prize.meters["loss"] += 1.0
        hero.memes["fear"] += 1.0
        world.say(
            f"The shortcut broke under {hero.id}'s feet, and {hero.id} had to cling to a root while the prize slipped into the dark."
        )
        world.say(
            f"Only then did {hero.id} learn that the old words were true: a warning is not a net to ignore, but a bridge to obey."
        )
        world.say(
            f"So {hero.id} went home without {prize.it()}, carrying the lesson more carefully than any gold."
        )

    world.facts.update(hero=hero, elder=elder, prize=prize, quest=quest, guide=guide, setting=setting)
    return world


SETTINGS = {
    "cliff": Setting(
        place="the cliff shrine",
        path="definite path",
        danger="the gullies",
        affords={"river", "cave"},
    ),
    "grove": Setting(
        place="the moon grove",
        path="definite path",
        danger="the briars",
        affords={"cave", "night"},
    ),
    "ford": Setting(
        place="the river ford",
        path="definite path",
        danger="the deep water",
        affords={"river", "night"},
    ),
}

QUESTS = {
    "river": Quest(
        id="river",
        verb="cross the river",
        gerund="crossing the river",
        rush="dash into the water",
        danger="cold and fast",
        risk="swept away",
        zone={"feet", "legs"},
        keyword="boldness",
        tags={"water", "lesson"},
    ),
    "cave": Quest(
        id="cave",
        verb="enter the cave",
        gerund="entering the cave",
        rush="run into the dark mouth",
        danger="hollow and echoing",
        risk="lost in the stone",
        zone={"torso", "head"},
        keyword="courage",
        tags={"dark", "lesson"},
    ),
    "night": Quest(
        id="night",
        verb="travel by night",
        gerund="traveling by night",
        rush="follow the unlit road",
        danger="without lamps",
        risk="wandered far",
        zone={"feet", "legs", "torso"},
        keyword="pride",
        tags={"dark", "lesson"},
    ),
}

PRIZES = {
    "cup": Prize(
        label="sun-cup",
        phrase="the sun-cup of morning",
        type="cup",
        region="hands",
    ),
    "cloak": Prize(
        label="blue cloak",
        phrase="a blue cloak of woven reeds",
        type="cloak",
        region="torso",
    ),
    "ring": Prize(
        label="stone ring",
        phrase="a stone ring of remembrance",
        type="ring",
        region="hands",
        genders={"girl", "boy"},
    ),
}

GUIDES = [
    Guide(
        id="elder",
        label="the elder",
        warning="definite",
        safe="Take the definite path; it remembers dry feet.",
        tail="the path held firm, and no step was taken by chance",
        lesson="walk with the warning, not the boast",
    ),
    Guide(
        id="none",
        label="no one",
        warning="soft",
        safe="",
        tail="",
        lesson="",
    ),
]

NAMES = ["Rob", "Mira", "Talen", "Ivo", "Nora", "Lio", "Sera"]
TRAITS = ["freckled", "little", "brave", "curious", "stubborn"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary myth world about a freckled child named Rob.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    quest_choices = sorted(SETTINGS[setting].affords)
    quest = args.quest or rng.choice(quest_choices)
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    if args.gender and args.prize and args.gender not in PRIZES[prize].genders:
        raise StoryError("That prize does not fit that hero here.")
    name = args.name or (args.name if args.name else ("Rob" if rng.random() < 0.5 else rng.choice(NAMES)))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, prize=prize, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children that includes the word "definite" and the name {f["hero"].id}.',
        f"Tell a cautionary tale about {f['hero'].id}, called Freckle, who hears a warning at {f['setting'].place}.",
        f"Write a mythic story where a small hero must choose the definite path instead of a dangerous shortcut.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    prize: Entity = f["prize"]
    quest: Quest = f["quest"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, the freckled child who tried to follow a dangerous desire and then learned to listen.",
        ),
        QAItem(
            question=f"What warning did {elder.label} give?",
            answer=f"{elder.label.capitalize()} gave a definite warning: take the {setting.path} and avoid {setting.danger}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {quest.verb}, even though the old road was risky.",
        ),
        QAItem(
            question=f"What changed at the end of the myth?",
            answer=f"{hero.id} chose the {setting.path}, returned with {prize.phrase}, and learned that caution can save a life.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a warning do?",
            answer="A warning tells someone about danger before they step into it, so they can choose a safer path.",
        ),
        QAItem(
            question="What is a definite path?",
            answer="A definite path is a clear and certain way to go, instead of a risky guess or shortcut.",
        ),
        QAItem(
            question="Why do myths often teach lessons?",
            answer="Myths often teach lessons because they use memorable stories to show children what choices are wise or unwise.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
warning(definite).
at_risk(Q,P) :- quest(Q), prize(P), zone(Q,R), region(P,R).
safe(Q,P) :- at_risk(Q,P), guide(g), definite_warning(g), path_choice(Q).
cautionary_story(S) :- hero(S), warning(definite).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("path_choice", sid))
        for q in s.affords:
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for z in q.zone:
            lines.append(asp.fact("zone", qid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
    lines.append(asp.fact("guide", "g"))
    lines.append(asp.fact("definite_warning", "g"))
    for g in GUIDES:
        lines.append(asp.fact("guide_id", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show safe/2.")
    model = asp.one_model(program)
    asp_safe = set(asp.atoms(model, "safe"))
    py_safe = set()
    for sid, s in SETTINGS.items():
        for qid in s.affords:
            q = QUESTS[qid]
            for pid, p in PRIZES.items():
                if _is_at_risk(q, p):
                    py_safe.add((qid, pid))
    if asp_safe == py_safe:
        print(f"OK: clingo gate matches Python reasoner ({len(py_safe)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(asp_safe - py_safe))
    print("only in python:", sorted(py_safe - asp_safe))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for qid in s.affords:
            q = QUESTS[qid]
            for pid, p in PRIZES.items():
                if _is_at_risk(q, p):
                    combos.append((sid, qid, pid))
    return combos


def explain_rejection(setting: Setting, quest: Quest, prize: Prize) -> str:
    if not _is_at_risk(quest, prize):
        return (
            f"(No story: {quest.gerund} does not endanger {prize.label} on the {prize.region}, "
            f"so there is no honest cautionary turn here.)"
        )
    return "(No story: this seed is too weak for the mythic cautionary pattern.)"


def select_seed_name(gender: str, rng: random.Random) -> str:
    if gender == "boy":
        return "Rob"
    return rng.choice([n for n in NAMES if n != "Rob"])


def valid_filtered(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    out = []
    for sid, qid, pid in valid_combos():
        if args.setting and sid != args.setting:
            continue
        if args.quest and qid != args.quest:
            continue
        if args.prize and pid != args.prize:
            continue
        out.append((sid, qid, pid))
    return out


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    prize_cfg = PRIZES[params.prize]
    guide = GUIDES[0]
    world = tell(setting, quest, prize_cfg, params.name, params.gender, guide)
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
    StoryParams(setting="ford", quest="river", prize="cloak", name="Rob", gender="boy", trait="freckled"),
    StoryParams(setting="cliff", quest="cave", prize="ring", name="Mira", gender="girl", trait="curious"),
    StoryParams(setting="grove", quest="night", prize="cup", name="Rob", gender="boy", trait="stubborn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe/2."))
        pairs = sorted(set(asp.atoms(model, "safe")))
        print(f"{len(pairs)} safe pairs:")
        for qid, pid in pairs:
            print(f"  {qid} {pid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            setting = args.setting or rng.choice(list(SETTINGS))
            quest = args.quest or rng.choice(sorted(SETTINGS[setting].affords))
            prize = args.prize or rng.choice(list(PRIZES))
            if not _is_at_risk(QUESTS[quest], PRIZES[prize]):
                if args.setting or args.quest or args.prize:
                    raise StoryError(explain_rejection(SETTINGS[setting], QUESTS[quest], PRIZES[prize]))
                continue
            gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
            if args.gender and args.prize and args.gender not in PRIZES[prize].genders:
                raise StoryError("That prize does not fit that hero here.")
            name = args.name or select_seed_name(gender, rng)
            trait = args.trait or rng.choice(TRAITS)
            params = StoryParams(setting=setting, quest=quest, prize=prize, name=name, gender=gender, trait=trait, seed=seed)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
