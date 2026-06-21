#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shrunken_dwell_numerous_curiosity_slice_of_life.py
===================================================================================

A small slice-of-life storyworld about a child's curiosity, a shrunken beloved
item, numerous little details at home, and the gentle way grown-ups help things
make sense again.

Seed words: shrunken, dwell, numerous
Feature: Curiosity
Style: Slice of Life
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CURIOSITY_INIT = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    dwelling: str
    has_window: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    heat: bool
    water: bool
    clothes: bool
    note: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    material: str
    region: str
    shrinkable: bool = False
    mended: bool = False
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


@dataclass
class StoryParams:
    setting: str = "kitchen"
    cause: str = "hot_wash"
    item: str = "wool_sweater"
    response: str = "gentle_fix"
    child_name: str = "Maya"
    child_gender: str = "girl"
    helper_name: str = "Grandma"
    helper_gender: str = "grandmother"
    seed: Optional[int] = None


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


def _lazy_asp():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import asp  # type: ignore
    return asp


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, cause in CAUSES.items():
            for iid, item in ITEMS.items():
                if is_reasonable(setting, cause, item):
                    combos.append((sid, cid, iid))
    return combos


def is_reasonable(setting: Setting, cause: Cause, item: Item) -> bool:
    return item.shrinkable and ((cause.water and item.material in {"wool", "cotton"}) or cause.heat)


def _r_curious(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("curiosity", 0.0) >= THRESHOLD and not world.fired.intersection({("curious", "asked")}):
        world.fired.add(("curious", "asked"))
        out.append("__ask__")
    return out


def _r_mood(world: World) -> list[str]:
    out = []
    item = world.get("item")
    if item.meters.get("shrunken", 0.0) >= THRESHOLD and not world.fired.intersection({("mood", "noticed")}):
        world.fired.add(("mood", "noticed"))
        child = world.get("child")
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        out.append(f"{child.id} noticed {item.label} had changed.")
    return out


CAUSAL_RULES = [_r_curious, _r_mood]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, cause: Cause, item: Item, response: Response,
         child_name: str = "Maya", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child",
        traits=["curious"], memes={"curiosity": CURIOSITY_INIT, "joy": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        traits=["gentle"], memes={"patience": 4.0},
    ))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    the_item = world.add(Entity(
        id="item", type="thing", type="thing", label=item.label, plural=False,
        meters={}, memes={}, attrs={"material": item.material, "region": item.region},
    ))

    world.say(
        f"On a quiet afternoon, {child.id} lived in {setting.place}, where "
        f"{setting.detail}."
    )
    world.say(
        f"{setting.dwelling.capitalize()} seemed full of {setting.tags and 'small, ordinary' or 'ordinary'} "
        f"things, and {child.id} liked to notice {setting.place} in a careful way."
    )
    world.say(
        f"One day, {child.id} found {item.phrase}. It looked shrunken, as if it had "
        f"been folded into a smaller story than yesterday."
    )

    world.para()
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} leaned closer and asked, \"Why did it get so tiny?\" "
        f"The question was bigger than the sweater."
    )
    if cause.note:
        world.say(cause.note)

    the_item.meters["shrunken"] += 1
    propagate(world)

    world.para()
    world.say(
        f"{helper.id} came over with a calm smile and showed {child.id} the truth "
        f"of it: the laundry had used the wrong kind of warmth, and wool could tighten up."
    )
    world.say(
        f'"That can happen," {helper.id} said softly. "Numerous little things dwell in '
        f"a home like this: labels, buttons, socks, and lessons. We can learn from them."'
    )

    contained = response.power >= 1
    if contained:
        world.para()
        the_item.meters["mended"] = 1.0
        world.say(
            f"{helper.id} {response.text.replace('{item}', item.label)}. "
            f"Then {helper.id} worked the cloth gently with warm hands until it "
            f"relaxed a little."
        )
        world.say(
            f"{child.id} watched closely and helped fold the edges. The sweater was "
            f"still a little shrunken, but now it fit like a cozy keep-sake instead of a surprise."
        )
        world.say(
            f"Before bed, {child.id} put it on a chair beside the window, where it "
            f"could dwell quietly and wait for tomorrow."
        )
    else:
        world.para()
        world.say(
            f"{helper.id} tried to help, but {response.fail.replace('{item}', item.label)}."
        )
        world.say(
            f"Still, {child.id} learned that curiosity can be patient, and some things "
            f"need a calmer plan than a quick fix."
        )

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        cause=cause,
        item_cfg=item,
        item=the_item,
        response=response,
        outcome="fixed" if contained else "imperfect",
    )
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item_cfg"]
    return [
        f'Write a slice-of-life story for a young child that includes the words '
        f'"shrunken", "dwell", and "numerous".',
        f"Tell a gentle story where {child.id} notices {item.phrase} looks "
        f"shrunken and asks why, then learns something everyday from a helper.",
        f'Write a cozy home story about curiosity, with a small surprise and a '
        f"calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, item, setting = f["child"], f["helper"], f["item"], f["setting"]
    out = [
        QAItem(
            question="What is the story about?",
            answer=(
                f"It is about {child.id}, a curious child, and {helper.id}, who "
                f"helped explain why {item.label} had changed. The story stays close "
                f"to an ordinary home day."
            ),
        ),
        QAItem(
            question=f"What did {child.id} notice?",
            answer=(
                f"{child.id} noticed that {item.phrase} looked shrunken. That made "
                f"{child.id} curious enough to ask a question right away."
            ),
        ),
        QAItem(
            question="How did the helper respond?",
            answer=(
                f"{helper.id} explained what had happened and helped carefully. "
                f"The calm answer turned the surprise into a small lesson."
            ),
        ),
    ]
    if f["outcome"] == "fixed":
        out.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"It ended gently, with the item still a little small but now "
                    f"understood and cared for. {child.id} learned something useful "
                    f"about how ordinary things can change at home."
                ),
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer=(
                "Curiosity is the feeling that makes you want to ask questions and "
                "learn why something happened. It helps children notice the world."
            ),
        ),
        QAItem(
            question="What does shrunken mean?",
            answer=(
                "Shrunken means smaller than it used to be. Clothes can become "
                "shrunken after washing or drying."
            ),
        ),
        QAItem(
            question="What does dwell mean?",
            answer=(
                "Dwell means to live or stay in a place. People, pets, and tiny "
                "things can dwell somewhere for a while."
            ),
        ),
        QAItem(
            question="What does numerous mean?",
            answer=(
                "Numerous means many. If there are numerous buttons in a box, there "
                "are lots of them."
            ),
        ),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        detail="sunlight drifted over the table, and tea towels hung near the sink",
        dwelling="this little kitchen",
        tags={"home", "window"},
    ),
    "laundry_room": Setting(
        id="laundry_room",
        place="the laundry room",
        detail="the washer hummed softly and baskets sat in neat stacks",
        dwelling="this bright room",
        tags={"home", "washing"},
    ),
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        detail="a lamp glowed beside a bed with a tucked blanket and a book on the pillow",
        dwelling="this small room",
        tags={"home", "quiet"},
    ),
}

CAUSES = {
    "hot_wash": Cause(
        id="hot_wash",
        label="a hot wash",
        heat=True,
        water=True,
        clothes=True,
        note="The sweater had gone through hot water and spin, which can make wool tighten and curl.",
        tags={"washing", "clothes"},
    ),
    "dryer_heat": Cause(
        id="dryer_heat",
        label="the dryer heat",
        heat=True,
        water=False,
        clothes=True,
        note="The dryer had been too warm for wool, so the fibers drew in close together.",
        tags={"washing", "clothes"},
    ),
}

ITEMS = {
    "wool_sweater": Item(
        id="wool_sweater",
        label="sweater",
        phrase="the wool sweater",
        material="wool",
        region="torso",
        shrinkable=True,
        tags={"clothes", "wool"},
    ),
    "cotton_hat": Item(
        id="cotton_hat",
        label="hat",
        phrase="the cotton hat",
        material="cotton",
        region="head",
        shrinkable=True,
        tags={"clothes", "cotton"},
    ),
    "tiny_towel": Item(
        id="tiny_towel",
        label="towel",
        phrase="the soft towel",
        material="cotton",
        region="hands",
        shrinkable=True,
        tags={"cloth", "cotton"},
    ),
}

RESPONSES = {
    "gentle_fix": Response(
        id="gentle_fix",
        sense=3,
        power=3,
        text="folded it into a bowl of warm water and eased the fibers out a little",
        fail="couldn't gently reshape it",
        qa_text="folded it into warm water and eased the fibers out a little",
        tags={"repair", "clothes"},
    ),
    "repurpose": Response(
        id="repurpose",
        sense=3,
        power=2,
        text="turned it into a soft pillow cover so the cloth could keep helping",
        fail="couldn't turn it into something useful",
        qa_text="turned it into a soft pillow cover",
        tags={"repair", "home"},
    ),
}

GIRL_NAMES = ["Maya", "Lena", "Iris", "Nina", "Sofia"]
BOY_NAMES = ["Owen", "Noah", "Theo", "Eli", "Finn"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.cause is None or c[1] == args.cause)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, cause, item = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or "Grandma"
    helper_gender = args.helper_gender or "grandmother"
    return StoryParams(
        setting=setting,
        cause=cause,
        item=item,
        response=response,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.cause not in CAUSES:
        raise StoryError("Unknown cause.")
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")

    setting = SETTINGS[params.setting]
    cause = CAUSES[params.cause]
    item = ITEMS[params.item]
    response = RESPONSES[params.response]
    if not is_reasonable(setting, cause, item):
        raise StoryError("This combination does not produce a reasonable slice-of-life story.")

    world = tell(setting, cause, item, response, params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life storyworld about curiosity, a shrunken item, and a gentle fix."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["grandmother", "grandfather"])
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


def asp_facts() -> str:
    asp = _lazy_asp()
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if c.heat:
            lines.append(asp.fact("heat", cid))
        if c.water:
            lines.append(asp.fact("water", cid))
        if c.clothes:
            lines.append(asp.fact("clothes", cid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.shrinkable:
            lines.append(asp.fact("shrinkable", iid))
        lines.append(asp.fact("material", iid, it.material))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S, C, I) :- setting(S), cause(C), item(I), shrinkable(I),
                       (heat(C); water(C)), material(I, wool).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    asp = _lazy_asp()
    model = asp.one_model(asp_program(show="#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, cause=None, item=None, response=None,
            child_name=None, gender=None, helper_name=None, helper_gender=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
    StoryParams(
        setting="kitchen",
        cause="hot_wash",
        item="wool_sweater",
        response="gentle_fix",
        child_name="Maya",
        child_gender="girl",
        helper_name="Grandma",
        helper_gender="grandmother",
    ),
    StoryParams(
        setting="laundry_room",
        cause="dryer_heat",
        item="cotton_hat",
        response="repurpose",
        child_name="Owen",
        child_gender="boy",
        helper_name="Grandma",
        helper_gender="grandmother",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable combos:")
        for s, c, i in combos:
            print(f"  {s:12} {c:12} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name}: {p.item} / {p.cause} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
