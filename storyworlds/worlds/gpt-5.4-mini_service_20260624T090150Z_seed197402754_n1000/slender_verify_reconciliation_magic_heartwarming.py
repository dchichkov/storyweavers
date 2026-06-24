#!/usr/bin/env python3
"""
A heartwarming storyworld about a slender magic keepsake, a small hurt, and a
gentle reconciliation.

Seed premise:
- A child treasures a slender magic object.
- A conflict arises when someone mishandles it.
- The family verifies the risk, chooses a safer magical act, and mends feelings.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    fragile: bool = False
    slender: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the cozy kitchen"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Magic:
    id: str
    label: str
    prep: str
    tail: str
    effect: str
    requires: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "kitchen": Setting(place="the cozy kitchen", indoors=True, affords={"share", "magic"}),
    "living_room": Setting(place="the sunny living room", indoors=True, affords={"share", "magic"}),
    "garden": Setting(place="the little garden", indoors=False, affords={"share", "magic"}),
}

ACTIVITIES = {
    "share": Activity(
        id="share",
        verb="share the magic thing",
        gerund="sharing the magic thing",
        rush="reach for it too fast",
        risk="might bend the slender wand",
        keyword="share",
        tags={"reconciliation"},
    ),
    "magic": Activity(
        id="magic",
        verb="do a magic trick",
        gerund="doing magic tricks",
        rush="wave it hard",
        risk="might wobble and snap",
        keyword="magic",
        tags={"magic"},
    ),
}

PRIZES = {
    "wand": Prize(
        label="wand",
        phrase="a slender magic wand",
        type="wand",
    ),
    "lantern": Prize(
        label="lantern",
        phrase="a paper lantern with silver stars",
        type="lantern",
    ),
}

MAGICS = {
    "gentle_glow": Magic(
        id="gentle_glow",
        label="a gentle glow spell",
        prep="hold the wand softly and whisper a tiny spell",
        tail="the wand stayed safe while the lantern glowed like a moonbeam",
        effect="glow",
        requires="wand",
    ),
    "paper_stars": Magic(
        id="paper_stars",
        label="a paper stars spell",
        prep="fold paper stars together",
        tail="the whole room shone with shared paper stars",
        effect="reconcile",
        requires="lantern",
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Ivy", "Ella"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                if act == "magic" and prize == "wand":
                    out.append((place, act, prize))
                if act == "share" and prize in {"wand", "lantern"}:
                    out.append((place, act, prize))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    sibling_name: str
    sibling_gender: str
    seed: Optional[int] = None


def _risk(world: World, hero: Entity, activity: Activity, prize: Entity) -> bool:
    return prize.label == "wand" and activity.id in {"share", "magic"}


def select_magic(activity: Activity, prize: Prize) -> Optional[Magic]:
    if activity.id == "magic" and prize.label == "wand":
        return MAGICS["gentle_glow"]
    if activity.id == "share" and prize.label == "lantern":
        return MAGICS["paper_stars"]
    return None


def predict(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"broken": bool(prize.meters.get("break", 0) >= THRESHOLD)}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    prize = world.get("prize")
    if activity.id == "magic":
        actor.memes["hope"] = actor.memes.get("hope", 0) + 1
        if prize.slender:
            prize.meters["wobble"] = prize.meters.get("wobble", 0) + 1
        if prize.slender and prize.meters["wobble"] >= THRESHOLD:
            prize.meters["break"] = prize.meters.get("break", 0) + 1
    else:
        actor.memes["want"] = actor.memes.get("want", 0) + 1
    if narrate:
        world.say(f"{actor.id} wanted to {activity.verb}.")


def propagate(world: World) -> None:
    prize = world.get("prize")
    for child in world.characters():
        if child.memes.get("snatched", 0) >= THRESHOLD and child.memes.get("hurt", 0) < THRESHOLD:
            child.memes["hurt"] = 1
            world.say(f"{child.id} felt hurt and quiet.")
        if child.memes.get("hurt", 0) >= THRESHOLD and child.memes.get("softened", 0) >= THRESHOLD:
            child.memes["reconciled"] = 1
            child.memes["hurt"] = 0
            world.say(f"{child.id}'s heart softened again.")
    if prize.meters.get("break", 0) >= THRESHOLD:
        world.say("The slender wand looked too bent to be happy.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_gender: str, sibling_name: str, sibling_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    sibling = world.add(Entity(id=sibling_name, kind="character", type=sibling_gender))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=hero.id, slender=True, fragile=True,
    ))
    world.add(Entity(id="parent", kind="character", type="mother"))
    hero.memes["love"] = 1
    sibling.memes["curious"] = 1
    world.say(f"{hero.id} loved {prize.phrase}, because it felt like a little piece of magic.")
    world.say(f"{hero.id}'s {('sister' if sibling_gender == 'girl' else 'brother')} {sibling.id} watched with shining eyes.")
    world.para()
    world.say(f"One afternoon in {setting.place}, {hero.id} and {sibling.id} sat near a small table.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {sibling.id} reached out too fast.")
    sibling.memes["snatched"] = 1
    if predict(world, hero, activity, "prize")["broken"]:
        world.say(f"{hero.id}'s {('mom' if hero_gender == 'girl' else 'dad')} said, \"Let's verify first before we wave that slender wand.\"")
    do_activity(world, hero, activity, narrate=False)
    if prize.meters.get("break", 0) >= THRESHOLD:
        world.say(f"The wand wobbled in {hero.id}'s hands, and everyone froze.")
    world.say(f"{sibling.id} looked sorry and lowered {sibling.pronoun('possessive')} hands.")
    sibling.memes["softened"] = 1
    propagate(world)
    world.para()
    magic = select_magic(activity, prize_cfg)
    if magic:
        world.say(f"{hero.id}'s parent smiled and offered {magic.label}.")
        world.say(f"\"We can {magic.prep},\" they said, \"and still keep the magic gentle.\"")
        world.say(f"Together they {magic.tail}.")
        sibling.memes["reconciled"] = 1
        hero.memes["reconciled"] = 1
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        sibling.memes["joy"] = sibling.memes.get("joy", 0) + 1
        world.say(f"{hero.id} and {sibling.id} smiled at each other, because the best magic was sharing.")
    else:
        world.say("They chose a calmer game and saved the special thing for another day.")
    world.facts.update(hero=hero, sibling=sibling, prize=prize, activity=activity, setting=setting, magic=magic)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about {f["hero"].id}, a slender magic wand, and a gentle reconciliation.',
        f"Tell a simple story where {f['hero'].id} and {f['sibling'].id} almost break a slender wand, then verify a safer magical choice.",
        f'Write a cozy story using the words "slender" and "verify" with a warm magical ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    prize = f["prize"]
    act = f["activity"]
    magic = f["magic"]
    qs = [
        QAItem(
            question=f"What did {hero.id} treasure in the story?",
            answer=f"{hero.id} treasured {prize.phrase}. It felt special because it was slender and magical.",
        ),
        QAItem(
            question=f"Why did the family want to verify before using it?",
            answer=f"They wanted to verify because {act.risk}, and they did not want the slender wand to get hurt.",
        ),
        QAItem(
            question=f"How did {hero.id} and {sibling.id} end up feeling about each other?",
            answer=f"They ended up reconciled and happy. The gentle magic helped them smile again and share kindly.",
        ),
    ]
    if magic:
        qs.append(QAItem(
            question=f"What safer magic did they use instead?",
            answer=f"They used {magic.label}, which let them keep the magic gentle and still enjoy the evening together.",
        ))
    return qs


KNOWLEDGE = {
    "slender": [
        QAItem(
            question="What does slender mean?",
            answer="Slender means thin and delicate, like something small that could bend easily if handled roughly.",
        )
    ],
    "magic": [
        QAItem(
            question="What is a magic trick?",
            answer="A magic trick is a special act that looks surprising, like making something glow or disappear.",
        )
    ],
    "verify": [
        QAItem(
            question="What does it mean to verify something?",
            answer="To verify something means to check carefully and make sure it is true or safe before you decide.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop feeling upset and become friendly with each other again.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    return [q for k in ("slender", "magic", "verify", "reconciliation") for q in KNOWLEDGE[k]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_risky(A,P) :- activity(A), prize(P), risky_pair(A,P).
need_verify(A,P) :- prize_risky(A,P).
can_reconcile(P) :- prize(P), slender(P).
valid_story(Place,A,P) :- setting(Place), affords(Place,A), prize_risky(A,P), can_reconcile(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.label == "wand":
            lines.append(asp.fact("slender", pid))
        for aid in ACTIVITIES:
            if pid == "wand" and aid in {"magic", "share"}:
                lines.append(asp.fact("risky_pair", aid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid stories.")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming slender-magic reconciliation storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    sibling_gender = args.sibling_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling_name = args.sibling_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    return StoryParams(place, activity, prize, name, gender, sibling_name, sibling_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.sibling_name,
        params.sibling_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.slender:
            bits.append("slender=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams("kitchen", "magic", "wand", "Mia", "girl", "Noah", "boy"),
    StoryParams("living_room", "share", "wand", "Leo", "boy", "Ivy", "girl"),
    StoryParams("garden", "magic", "wand", "Ava", "girl", "Finn", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        models = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(models, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
