#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/speaker_sound_effects_sharing_dialogue_folk_tale.py
====================================================================================

A standalone story world for a tiny folk-tale domain about a village speaker,
a shared sound-making object, a warning, a quarrel, and a kind resolution.

The domain is built around:
- a speaker used to make sound effects for a story time or festival
- sharing between children or neighbors
- dialogue that resolves a misunderstanding
- a folk-tale mood: simple, rhythmic, concrete, and a little magical

The world model tracks physical meters and emotional memes. A small causal engine
drives the prose from state changes, and a declarative ASP twin mirrors the
reasonableness gate and ending choice.
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
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "gran", "grandfather": "granpa"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    detail: str


@dataclass
class SoundThing:
    id: str
    label: str
    phrase: str
    effect: str
    safe_share: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    breakable: bool = False
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["tension"] += 1
        out.append("__tension__")
    return out


def _r_shame(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes["tension"] < THRESHOLD:
            continue
        if ch.role != "share-holder":
            continue
        sig = ("shame", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["sad"] += 1
        out.append(f"{ch.id} felt the sting of the broken moment.")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("shame", "social", _r_shame)]


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


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def hazard_at_risk(tool: SoundThing, item: ShareItem) -> bool:
    return tool.safe_share and item.fragile is False


def sound_choice(tool: SoundThing, action: str) -> str:
    return f"{tool.effect} {action}"


def predict(world: World, share_id: str) -> dict:
    sim = world.copy()
    _do_spill(sim, sim.get(share_id), narrate=False)
    return {
        "spilled": sim.get(share_id).meters["spilled"] >= THRESHOLD,
        "tension": sum(ch.memes["tension"] for ch in sim.characters()),
    }


def _do_spill(world: World, item: Entity, narrate: bool = True) -> None:
    item.meters["spilled"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, other: Entity, setting: Setting, tool: SoundThing) -> None:
    child.memes["joy"] += 1
    other.memes["joy"] += 1
    world.say(
        f"In {setting.place}, where {setting.mood} winds moved through the trees, "
        f"{child.id} and {other.id} found a little {tool.label}. {setting.detail}"
    )
    world.say(
        f'"Listen," said {child.id}, "when I tap it, it can go {tool.effect}!"'
    )


def want_turn(world: World, child: Entity, other: Entity, tool: SoundThing, item: ShareItem) -> None:
    child.memes["want"] += 1
    world.say(
        f"{child.id} wanted to keep the {tool.label} all to {child.pronoun('possessive')}self, "
        f"because the sound was so bright and funny."
    )
    world.say(
        f"But {other.id} looked at the shared {item.label} and said, "
        f"\"Good friend, a thing that makes a song should be heard by two hearts.\""
    )


def argue(world: World, child: Entity, other: Entity, tool: SoundThing) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"No," said {child.id}. "It is mine!" {sound_choice(tool, "came again")}, '
        f"and the little sound bounced off the stones."
    )
    world.say(
        f"{other.id} bit {other.pronoun('possessive')} lip, for {child.id}'s voice had turned sharp."
    )


def share_warning(world: World, other: Entity, child: Entity, tool: SoundThing, item: ShareItem) -> None:
    pred = predict(world, item.id)
    other.memes["care"] += 1
    world.facts["predicted_tension"] = pred["tension"]
    world.say(
        f'"If you keep pulling on it," said {other.id}, "the {item.label} may fall, '
        f"and then the merry moment will turn small and sad."
    )


def misuse(world: World, child: Entity, item: ShareItem) -> None:
    _do_spill(world, item)
    world.say(
        f"At last {child.id} tugged too hard. The {item.label} slipped, and the music-sound "
        f"turned into a startled clatter."
    )


def alarm(world: World, other: Entity, child: Entity, item: ShareItem) -> None:
    world.say(
        f'"Oh!" cried {other.id}. "The {item.label}!"'
    )
    world.say(
        f"{child.id} froze, hearing how loud a broken thing can sound in a quiet hour."
    )


def calm_fix(world: World, elder: Entity, child: Entity, item: ShareItem, response: Response) -> None:
    item_ent = world.get(item.id)
    item_ent.meters["spilled"] = 0
    world.say(
        f"{elder.id} came beside them at once. {elder.pronoun().capitalize()} {response.text}."
    )
    world.say(
        f"The old trouble was swept away, and the room grew still enough for clear words."
    )


def lesson(world: World, elder: Entity, child: Entity, other: Entity, tool: SoundThing) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    other.memes["love"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {elder.id} smiled and said, \"A song is sweeter when it is shared.\" "
        f"{child.id} nodded, and {other.id} nodded too."
    )
    world.say(
        f'"I promise," said {child.id}, "to let the sound be a shared one."'
    )


def ending_gift(world: World, elder: Entity, child: Entity, other: Entity, tool: SoundThing) -> None:
    for ch in (child, other):
        ch.memes["joy"] += 1
    world.say(
        f"The next day, {elder.id} brought out a second little wooden {tool.label} "
        f"so each child could hold one."
    )
    world.say(
        f"Then the pair played side by side: {tool.effect}, {tool.effect}, "
        f"like birds answering birds at dusk."
    )
    world.say(
        f"And so the two friends shared the sound, and the village remembered the kind answer."
    )


def tell(setting: Setting, tool: SoundThing, item: ShareItem, response: Response,
         child_name: str = "Mila", child_gender: str = "girl",
         other_name: str = "Jon", other_gender: str = "boy",
         elder_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="share-holder"))
    other = world.add(Entity(id=other_name, kind="character", type=other_gender, role="listener"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder"))
    item_ent = world.add(Entity(id=item.id, kind="thing", type="thing", label=item.label, role="shared"))
    item_ent.meters["spilled"] = 0
    world.facts["setting"] = setting
    world.facts["tool"] = tool
    world.facts["item"] = item
    world.facts["response"] = response
    world.facts["child"] = child
    world.facts["other"] = other
    world.facts["elder"] = elder

    setup(world, child, other, setting, tool)
    world.para()
    want_turn(world, child, other, tool, item)
    share_warning(world, other, child, tool, item)
    argue(world, child, other, tool)
    misuse(world, child, item)
    alarm(world, other, child, item)
    world.para()
    calm_fix(world, elder, child, item, response)
    lesson(world, elder, child, other, tool)
    world.para()
    ending_gift(world, elder, child, other, tool)

    world.facts["outcome"] = "repaired"
    return world


SETTINGS = {
    "village": Setting("village", "the village green", "soft", "The old well stood nearby, and the goose market was already quiet."),
    "meadow": Setting("meadow", "the meadow road", "gentle", "Wildflowers bent low, and a small brook sang at the edge."),
    "mill": Setting("mill", "the mill yard", "steady", "The mill wheel hummed like a sleepy drum."),
}

TOOLS = {
    "speaker": SoundThing("speaker", "speaker", "pop-pop", "pop-pop", safe_share=True, tags={"speaker", "sound"}),
    "drum": SoundThing("drum", "drum", "boom-boom", "boom-boom", safe_share=True, tags={"drum", "sound"}),
    "bell": SoundThing("bell", "bell", "ding-ding", "ding-ding", safe_share=True, tags={"bell", "sound"}),
}

ITEMS = {
    "cloak": ShareItem("cloak", "cloak", "the bright cloak", fragile=False, breakable=True, tags={"cloak"}),
    "cup": ShareItem("cup", "cup", "the little cup", fragile=False, breakable=True, tags={"cup"}),
    "banner": ShareItem("banner", "banner", "the festival banner", fragile=False, breakable=True, tags={"banner"}),
}

RESPONSES = {
    "mend": Response("mend", 3, 3, "mended the broken place with a steady hand", "tried to mend it, but the crack stayed loud and wide", "mended the broken place with a steady hand", tags={"repair"}),
    "wipe": Response("wipe", 3, 2, "wiped the spill clean with a cloth and a calm breath", "wiped and wiped, but the spill only spread more", "wiped the spill clean with a cloth and a calm breath", tags={"repair"}),
    "share": Response("share", 4, 4, "set a second one beside it, so both children could share the sound", "set out a second one, but the moment had already gone sour", "set a second one beside it, so both children could share the sound", tags={"share"}),
}

SENSE_MIN = 2

NAMES_G = ["Mila", "Sana", "Lina", "Rina", "Tara"]
NAMES_B = ["Jon", "Timo", "Evan", "Perry", "Noel"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, tool in TOOLS.items():
            for iid, item in ITEMS.items():
                if hazard_at_risk(tool, item):
                    combos.append((sid, tid, iid))
    return combos


@dataclass
class StoryParams:
    setting: str
    tool: str
    item: str
    response: str
    child: str
    child_gender: str
    other: str
    other_gender: str
    elder_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tool: SoundThing = f["tool"]
    item: ShareItem = f["item"]
    return [
        f'Write a folk-tale-style story for a young child that includes the word "{tool.label}" and a playful sound effect.',
        f"Tell a small sharing story where two children hear {tool.effect} and learn to share the {item.label}.",
        f"Write a gentle dialogue-driven tale about a {tool.label} that teaches sharing instead of keeping the sound all to one child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    other: Entity = f["other"]
    elder: Entity = f["elder"]
    tool: SoundThing = f["tool"]
    item: ShareItem = f["item"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {child.id}, {other.id}, and the little {tool.label} they found in the village. The sound led them into a lesson about sharing and kinder words."
        ),
        QAItem(
            question=f"What happened when {child.id} held the {tool.label} too tightly?",
            answer=f"The shared {item.label} slipped and made a startled clatter. That happened because the child was trying to keep the sound all to {child.pronoun('possessive')}self instead of sharing it."
        ),
        QAItem(
            question=f"How did {elder.id} help?",
            answer=f"{elder.id} came with a calm answer and {f['response'].qa_text}. The trouble settled because the grown-up chose a steady fix and turned the moment back toward sharing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: SoundThing = f["tool"]
    items = [
        QAItem(
            question="What is a speaker in a story like this?",
            answer="A speaker can be a small thing that makes sounds louder or clearer. In a folk tale, it can help children hear a game, a song, or a sound effect."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too. It is a kind choice because everyone gets a turn or a part."
        ),
        QAItem(
            question=f"What kind of sound does a {tool.label} make here?",
            answer=f"It makes a lively {tool.effect} sound, almost like a little drum made of wood and joy. The sound is fun, but it is better when it is shared."
        ),
    ]
    return items


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "speaker", "cloak", "mend", "Mila", "girl", "Jon", "boy", "grandmother"),
    StoryParams("meadow", "drum", "cup", "wipe", "Tara", "girl", "Noel", "boy", "grandmother"),
    StoryParams("mill", "bell", "banner", "share", "Sana", "girl", "Evan", "boy", "grandmother"),
]


def explain_rejection(tool: SoundThing, item: ShareItem) -> str:
    return f"(No story: the {tool.label} does not create a useful sharing problem with {item.label}.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {good}.)"


ASP_RULES = r"""
hazard(T, I) :- tool(T), item(I).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(repaired) :- chosen_response(R), response(R), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.safe_share:
            lines.append(asp.fact("safe_share", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1.\n#show sensible/1."))
    if set(asp.atoms(model, "sensible")) == {(r.id,) for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    sample = generate(CURATED[0])
    if not sample.story:
        rc = 1
        print("MISMATCH: normal generation produced empty story.")
    else:
        print("OK: smoke story generated.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a speaker, sharing, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--other")
    ap.add_argument("--elder-type", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, item = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = rng.choice(["girl", "boy"])
    other_gender = "boy" if child_gender == "girl" else "girl"
    child_pool = NAMES_G if child_gender == "girl" else NAMES_B
    other_pool = NAMES_B if other_gender == "boy" else NAMES_G
    child = args.child or rng.choice(child_pool)
    other = args.other or rng.choice([n for n in other_pool if n != child])
    elder = args.elder_type or rng.choice(["mother", "father", "grandmother"])
    return StoryParams(setting, tool, item, response, child, child_gender, other, other_gender, elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TOOLS[params.tool], ITEMS[params.item], RESPONSES[params.response],
                 params.child, params.child_gender, params.other, params.other_gender, params.elder_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
