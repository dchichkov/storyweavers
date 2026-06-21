#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/intuit_opposite_everywhere_sharing_sound_effects_magic.py
=========================================================================================

A small whodunit-style storyworld: a child notices something odd, a shared
magical object goes missing, clues are heard everywhere as sound effects, and
the characters solve the mystery by trusting intuition and doing the opposite of
the obvious thing.

The world is intentionally tiny and state-driven:
- a shared magic item can be passed around,
- loud sound effects reveal movement and timing,
- a simple "opposite" rule hides the clue in plain sight,
- the ending proves who had the item and where it was found.

The seed words are woven into both the premise and the narration:
intuit, opposite, everywhere.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        t = self.type
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if t in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if t in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    vibe: str
    has_hiding_spots: bool = True


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    sound: str
    opposite_hint: str
    can_share: bool = True
    magical: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueSpot:
    id: str
    label: str
    phrase: str
    clue_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    text: str
    sound: str
    effect: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    magic: str
    clue: str
    action: str
    detective_name: str
    detective_gender: str
    suspect_name: str
    suspect_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "library": Setting(id="library", place="the library", vibe="quiet shelves"),
    "museum": Setting(id="museum", place="the museum", vibe="echoing halls"),
    "attic": Setting(id="attic", place="the attic", vibe="dusty beams"),
}

MAGIC = {
    "wand": MagicItem(
        id="wand", label="wand", phrase="a silver wand", sound="fizz-fizz",
        opposite_hint="the wand always points where the answer is not", tags={"magic", "sharing"}
    ),
    "book": MagicItem(
        id="book", label="spellbook", phrase="an old spellbook", sound="flip-flip",
        opposite_hint="the spellbook hid the clue on the opposite page", tags={"magic", "sharing"}
    ),
    "bell": MagicItem(
        id="bell", label="bell", phrase="a tiny magic bell", sound="ding-ding",
        opposite_hint="the bell rang the opposite room when touched", tags={"magic", "sharing"}
    ),
}

CLUES = {
    "drawer": ClueSpot(id="drawer", label="drawer", phrase="the bottom drawer", clue_kind="hidden"),
    "glove": ClueSpot(id="glove", label="glove", phrase="a left glove", clue_kind="opposite"),
    "rug": ClueSpot(id="rug", label="rug", phrase="under the blue rug", clue_kind="everywhere"),
}

ACTIONS = {
    "share": Action(
        id="share", text="share the magic item", sound="tap-tap", effect="passed hands",
        sense=3, tags={"sharing", "magic"}
    ),
    "swap": Action(
        id="swap", text="do the opposite of the obvious thing", sound="whoosh",
        effect="changed sides", sense=3, tags={"opposite"}
    ),
    "search": Action(
        id="search", text="search everywhere", sound="step-step-step",
        effect="looked all around", sense=3, tags={"everywhere"}
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Rose", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Max", "Finn", "Eli", "Noah", "Sam"]
TRAITS = ["curious", "careful", "clever", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MAGIC:
            for c in CLUES:
                combos.append((s, m, c))
    return combos


def reasonableness(action: Action, magic: MagicItem, clue: ClueSpot) -> bool:
    return action.sense >= 2 and magic.magical and clue.clue_kind in {"hidden", "opposite", "everywhere"}


def explain_rejection() -> str:
    return "(No story: this setup does not support a fair whodunit mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with magic, sharing, sound effects, and clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = [args.setting] if args.setting else list(SETTINGS)
    magics = [args.magic] if args.magic else list(MAGIC)
    clues = [args.clue] if args.clue else list(CLUES)
    actions = [args.action] if args.action else list(ACTIONS)
    combos = [(s, m, c, a) for s in settings for m in magics for c in clues for a in actions
              if reasonableness(ACTIONS[a], MAGIC[m], CLUES[c])]
    if not combos:
        raise StoryError(explain_rejection())
    s, m, c, a = rng.choice(combos)
    dg = rng.choice(["girl", "boy"])
    sg = "boy" if dg == "girl" else "girl"
    hg = rng.choice(["girl", "boy"])
    return StoryParams(
        setting=s, magic=m, clue=c, action=a,
        detective_name=pick_name(rng, dg), detective_gender=dg,
        suspect_name=pick_name(rng, sg), suspect_gender=sg,
        helper_name=pick_name(rng, hg), helper_gender=hg,
    )


def _cue_sound(text: str) -> str:
    return f"{text} {text.lower()}"


def tell(params: StoryParams) -> World:
    w = World()
    setting = SETTINGS[params.setting]
    magic = MAGIC[params.magic]
    clue = CLUES[params.clue]
    action = ACTIONS[params.action]

    d = w.add(Entity(id=params.detective_name, kind="character", type=params.detective_gender, role="detective"))
    s = w.add(Entity(id=params.suspect_name, kind="character", type=params.suspect_gender, role="suspect"))
    h = w.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    item = w.add(Entity(id="magic", type="thing", label=magic.label, attrs={"holder": d.id}))
    spot = w.add(Entity(id="clue", type="thing", label=clue.label, attrs={"place": clue.phrase}))
    w.facts.update(setting=setting, magic=magic, clue=clue, action=action, detective=d, suspect=s, helper=h, item=item, spot=spot)

    d.memes["curiosity"] = 1
    w.say(
        f"At {setting.place}, {d.id} noticed something odd. {setting.vibe} felt normal, but the air did not."
    )
    w.say(
        f"{s.id} had been near {magic.phrase}, and {magic.sound} seemed to echo everywhere, as if the room itself was whispering."
    )
    w.para()
    w.say(
        f'{d.id} could intuit the opposite of the obvious clue: if the sound was heard everywhere, the thing was hidden where no one first looked.'
    )
    w.say(
        f'"Let us {action.text}," said {h.id}, and together they moved with {action.sound}.'
    )
    w.para()
    if action.id == "share":
        item.attrs["holder"] = h.id
        w.say(
            f"{d.id} shared the {magic.label} instead of clutching it alone. That was the opposite of what the thief expected."
        )
    elif action.id == "swap":
        item.attrs["holder"] = s.id
        w.say(
            f"They did the opposite of the obvious thing and checked the quiet place first. The sound in the halls made the answer feel closer."
        )
    else:
        w.say(
            f"{d.id}, {h.id}, and {s.id} searched everywhere. Every shelf, every rug, every corner answered with a little clue-sound."
        )

    if clue.id == "drawer":
        spot.attrs["found"] = "drawer"
        item.attrs["found"] = "drawer"
        w.say(
            f"Then came a sharp {magic.sound} from the drawer -- click, scratch, and a tiny flash. Inside was the missing thing."
        )
    elif clue.id == "glove":
        spot.attrs["found"] = "glove"
        item.attrs["found"] = "glove"
        w.say(
            f"On the opposite page of the room, under a lone glove, the clue glittered in a thin ribbon of magic."
        )
    else:
        spot.attrs["found"] = "rug"
        item.attrs["found"] = "rug"
        w.say(
            f"Everywhere they looked, the rug seemed to hum. At last they lifted it and found the missing piece waiting underneath."
        )

    w.para()
    w.say(
        f"{d.id} looked at {s.id} and knew the answer at once. The trick had been to share, listen for the sound, and trust the opposite clue."
    )
    w.say(
        f"{s.id} confessed and {h.id} handed the magic back. By bedtime, the whole mystery was solved, and {magic.label} was safe again in {d.id}'s hands."
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: MagicItem = f["magic"]
    return [
        f'Write a whodunit for a 3-to-5-year-old that includes the words "intuit", "opposite", and "everywhere".',
        f"Tell a short mystery where children share {m.phrase}, hear strange sound effects everywhere, and solve the clue by doing the opposite of the obvious thing.",
        f'Write a magical detective story with sharing and sound effects, where the answer is discovered by intuition and an opposite clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["detective"]
    s: Entity = f["suspect"]
    h: Entity = f["helper"]
    m: MagicItem = f["magic"]
    c: ClueSpot = f["clue"]
    a: Action = f["action"]
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{d.id} solved it with help from {h.id}. {d.id} listened carefully, noticed the clue, and figured out who had moved the magic item."
        ),
        QAItem(
            question="What made the mystery hard to guess?",
            answer=f"The clues seemed to be everywhere, because the sound effects echoed all through the room. That made the answer feel hidden until {d.id} thought of the opposite of the obvious idea."
        ),
        QAItem(
            question=f"What happened to {m.label} at the end?",
            answer=f"It was found again and handed back safely. The missing {m.label} was discovered near {c.phrase}, after the children shared the search instead of arguing."
        ),
        QAItem(
            question=f"Why did {s.id} get caught?",
            answer=f"{s.id} tried to keep the mystery simple, but the sound effects gave away the timing. When {d.id} intuitively checked the opposite place, the hiding spot stopped being secret."
        ),
        QAItem(
            question=f"What did {d.id} and {h.id} do to fix things?",
            answer=f"They shared the work, used a calm plan, and searched everywhere. That teamwork turned the strange magic into a solved mystery."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to intuit something?",
            answer="To intuit something means to guess it quickly from a feeling or a clue, even before you can explain every part of it."
        ),
        QAItem(
            question="What does opposite mean?",
            answer="Opposite means the other side, the reverse choice, or the thing that is not like the first one."
        ),
        QAItem(
            question="What does everywhere mean?",
            answer="Everywhere means all around, in every place you can look."
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use, hold, or enjoy something too."
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you hear the action, like tap, whoosh, or ding."
        ),
        QAItem(
            question="What does magic do in a story?",
            answer="Magic can make surprising things happen, like glowing clues or strange noises, so the mystery feels special."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {e.role} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
visible(opposite).
visible(everywhere).
visible(intuit).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MAGIC:
        lines.append(asp.fact("magic", mid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show magic/1.\n#show clue/1.\n"))
    s = asp.atoms(model, "setting")
    m = asp.atoms(model, "magic")
    c = asp.atoms(model, "clue")
    return sorted({(a[0], b[0], d[0]) for a in s for b in m for d in c})


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as e:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    for k in ("setting", "magic", "clue", "action"):
        if getattr(params, k) not in globals()[k.upper() if k != "action" else "ACTIONS"]:
            raise StoryError(f"invalid {k}: {getattr(params, k)}")
    if params.setting not in SETTINGS or params.magic not in MAGIC or params.clue not in CLUES or params.action not in ACTIONS:
        raise StoryError("invalid story parameters")
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
    StoryParams(setting="library", magic="wand", clue="drawer", action="share",
                detective_name="Lily", detective_gender="girl",
                suspect_name="Theo", suspect_gender="boy",
                helper_name="Mia", helper_gender="girl"),
    StoryParams(setting="museum", magic="book", clue="glove", action="swap",
                detective_name="Ben", detective_gender="boy",
                suspect_name="Ava", suspect_gender="girl",
                helper_name="Noah", helper_gender="boy"),
    StoryParams(setting="attic", magic="bell", clue="rug", action="search",
                detective_name="Nora", detective_gender="girl",
                suspect_name="Sam", suspect_gender="boy",
                helper_name="Eli", helper_gender="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = [args.setting] if args.setting else list(SETTINGS)
    magics = [args.magic] if args.magic else list(MAGIC)
    clues = [args.clue] if args.clue else list(CLUES)
    actions = [args.action] if args.action else list(ACTIONS)
    combos = [(s, m, c, a) for s in settings for m in magics for c in clues for a in actions if reasonableness(ACTIONS[a], MAGIC[m], CLUES[c])]
    if not combos:
        raise StoryError(explain_rejection())
    s, m, c, a = rng.choice(combos)
    dg = args.__dict__.get("detective_gender", None) or rng.choice(["girl", "boy"])
    sg = "boy" if dg == "girl" else "girl"
    hg = rng.choice(["girl", "boy"])
    return StoryParams(
        setting=s, magic=m, clue=c, action=a,
        detective_name=pick_name(rng, dg), detective_gender=dg,
        suspect_name=pick_name(rng, sg), suspect_gender=sg,
        helper_name=pick_name(rng, hg), helper_gender=hg,
    )


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1.\n#show magic/1.\n#show clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
