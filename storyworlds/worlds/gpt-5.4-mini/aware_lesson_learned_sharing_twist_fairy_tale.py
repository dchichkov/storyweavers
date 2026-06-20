#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aware_lesson_learned_sharing_twist_fairy_tale.py
=================================================================================

A standalone fairy-tale-style story world about a small kingdom, a shared treasure,
an "aware" child who notices a problem, and a twist ending where the learned lesson
changes how everyone behaves.

Base seed prompt
-----------------
Write a story that includes the following words and narrative instruments.
Words: aware
Features: Lesson Learned, Sharing, Twist
Style: Fairy Tale

World idea
----------
In this little domain, a child finds a magical fairing at a festival: a loaf of
honey bread, a ribboned lantern, or a basket of berries. One child wants to keep
it all, another child notices a hint of trouble, and an adult helper encourages
sharing. The twist is that the treasure turns out to be more generous than it
first seemed: when shared, it reveals a second gift, a hidden song, a doubled
glow, or a surprise blessing. The world model drives the prose through changing
physical meters and emotional memes.

The story world is designed to produce:
- a clear fairy-tale beginning,
- a tension beat about keeping vs. sharing,
- a state-driven twist,
- and an ending image that proves the lesson learned.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/aware_lesson_learned_sharing_twist_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/aware_lesson_learned_sharing_twist_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/aware_lesson_learned_sharing_twist_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/aware_lesson_learned_sharing_twist_fairy_tale.py --verify
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
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    gift: str
    shares_into: str
    glow: str
    hidden_twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
    festival: str
    ending_image: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["shared"] < THRESHOLD:
            continue
        sig = ("share", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        partner = world.facts.get("partner")
        if partner:
            partner.memes["joy"] += 1
        ent.memes["joy"] += 1
        out.append("__share__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    treasure: Treasure = world.facts["treasure_cfg"]
    gift = world.get("gift")
    if gift.meters["opened"] < THRESHOLD:
        return out
    sig = ("twist", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gift.meters["twisted"] += 1
    world.facts["twist_seen"] = True
    out.append("__twist__")
    return out


CAUSAL_RULES = [
    Rule("share", "social", _r_share),
    Rule("twist", "story", _r_twist),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(treasure: Treasure, setting: Setting) -> bool:
    return "shareable" in treasure.tags and "fairy" in setting.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def is_enough(response: Response, treasure: Treasure, delay: int) -> bool:
    return response.power >= (1 + delay)


def predict_twist(world: World, treasure_id: str) -> dict:
    sim = world.copy()
    _open_gift(sim, sim.get("gift"), narrate=False)
    return {
        "opened": sim.get("gift").meters["opened"] >= THRESHOLD,
        "twist": bool(sim.facts.get("twist_seen")),
    }


def _open_gift(world: World, gift: Entity, narrate: bool = True) -> None:
    gift.meters["opened"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, partner: Entity, setting: Setting, treasure: Treasure) -> None:
    child.memes["wonder"] += 1
    partner.memes["wonder"] += 1
    world.say(
        f"Once, in {setting.place}, {child.id} and {partner.id} came to {setting.festival}. "
        f"{setting.scene}"
    )
    world.say(
        f"They found {treasure.phrase}, and its smell was as sweet as a summer song."
    )


def aware_beat(world: World, partner: Entity, treasure: Treasure, setting: Setting) -> None:
    partner.memes["aware"] += 1
    world.say(
        f'{partner.id} grew aware of a small trouble. "If we keep it all, '
        f'our neighbors at {setting.dark_spot} will have nothing," '
        f"{partner.pronoun()} said."
    )


def keep_it_all(world: World, child: Entity, treasure: Treasure) -> None:
    child.memes["greedy"] += 1
    world.say(
        f'"It is mine," {child.id} said, holding the {treasure.label} close and '
        f'forgetting the other children by the gate.'
    )


def ask_share(world: World, partner: Entity, child: Entity, treasure: Treasure) -> None:
    partner.memes["courage"] += 1
    world.say(
        f'"Could we share it?" {partner.id} asked softly. '
        f'"A fair gift grows kinder when it is divided."'
    )


def twist_reveal(world: World, treasure: Treasure) -> None:
    gift = world.get("gift")
    gift.meters["opened"] += 1
    treasure.meters = treasure.meters  # no-op, keeps the treasure object in the live world
    world.say(
        f"When they broke the {treasure.label} open, a second delight appeared: "
        f"{treasure.hidden_twist}."
    )


def compromise(world: World, child: Entity, partner: Entity, treasure: Treasure) -> None:
    child.meters["shared"] += 1
    partner.meters["shared"] += 1
    propagate(world, narrate=False)
    child.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"{child.id} finally nodded. Together they shared the {treasure.label} with the rest."
    )


def ending(world: World, setting: Setting, child: Entity, partner: Entity, treasure: Treasure) -> None:
    child.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f"By nightfall, {treasure.gift} had reached every hand, and {setting.ending_image}."
    )
    world.say(
        f"{child.id} learned that sharing did not make the treasure smaller; "
        f"it made the kindness inside it easier to see."
    )


def tell(setting: Setting, treasure: Treasure, response: Response,
         child_name: str = "Mira", child_gender: str = "girl",
         partner_name: str = "Pip", partner_gender: str = "boy",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    gift = world.add(Entity(id="gift", type="thing", label=treasure.label))
    world.facts["partner"] = partner
    world.facts["treasure_cfg"] = treasure

    setup(world, child, partner, setting, treasure)
    world.para()
    aware_beat(world, partner, treasure, setting)
    keep_it_all(world, child, treasure)
    ask_share(world, partner, child, treasure)

    if child.memes["greedy"] > partner.memes["aware"]:
        world.say(
            f"{child.id} did not listen at first, and the festival lanterns seemed dimmer."
        )
    if is_enough(response, treasure, delay):
        compromise(world, child, partner, treasure)
        _open_gift(world, gift)
        twist_reveal(world, treasure)
        world.para()
        ending(world, setting, child, partner, treasure)
        outcome = "shared"
    else:
        world.say(
            f"The grown-up tried to help, but the moment had already gone cold."
        )
        outcome = "stalled"

    world.facts.update(
        child=child, partner=partner, gift=gift, setting=setting, treasure_cfg=treasure,
        response=response, outcome=outcome, twist_seen=bool(world.facts.get("twist_seen")),
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the moonlit meadow",
        scene="Silver flowers bowed as the fairfolk danced under the stars.",
        dark_spot="the old oak by the bridge",
        festival="the midsummer fair",
        ending_image="the lanterns shone brighter because everyone carried a little light",
        tags={"fairy", "festival"},
    ),
    "castle": Setting(
        id="castle",
        place="the castle hall",
        scene="Banners fluttered, and the harp music bounced off the gold stone walls.",
        dark_spot="the kitchen door",
        festival="the royal feast",
        ending_image="the hall glowed warm as every child shared a sweet bite",
        tags={"fairy", "feast"},
    ),
    "village": Setting(
        id="village",
        place="the village green",
        scene="The well had ribbons on it, and the bees made a sleepy hum around the pie cart.",
        dark_spot="the path beside the bakery",
        festival="the harvest gathering",
        ending_image="the evening bells rang while the neighbors smiled with full hearts",
        tags={"fairy", "gathering"},
    ),
}

TREASURES = {
    "bread": Treasure(
        id="bread",
        label="honey bread",
        phrase="a warm loaf of honey bread tied with a gold thread",
        gift="sweet crumbs",
        shares_into="little slices",
        glow="golden crust",
        hidden_twist="inside the loaf was a tiny sugar heart for each child",
        tags={"shareable", "sweet"},
    ),
    "lantern": Treasure(
        id="lantern",
        label="silver lantern",
        phrase="a silver lantern wrapped in blue ribbon",
        gift="soft light",
        shares_into="glimmers",
        glow="moon-bright glass",
        hidden_twist="the lantern held two flames that burned as one when shared",
        tags={"shareable", "light"},
    ),
    "berries": Treasure(
        id="berries",
        label="berry basket",
        phrase="a berry basket beaded with dew",
        gift="red juice",
        shares_into="bowls",
        glow="deep red shine",
        hidden_twist="under the berries sat a seed pouch for each friend",
        tags={"shareable", "fruit"},
    ),
}

RESPONSES = {
    "gentle": Response(
        "gentle", 3, 3,
        "smiled, lifted the treasure carefully, and helped everyone share it at once",
        "tried to share, but the moment had already slipped away",
        "smiled and helped everyone share it at once",
        tags={"share"},
    ),
    "song": Response(
        "song", 2, 2,
        "hummed a soft song, and the tune made the treasure easier to divide",
        "hummed, but the treasure stayed stubbornly closed",
        "hummed a soft song and made the treasure easier to divide",
        tags={"share", "song"},
    ),
    "basket": Response(
        "basket", 1, 1,
        "set the treasure in a basket and hoped that would solve everything",
        "set the treasure in a basket, but it was still not ready to be shared",
        "set the treasure in a basket",
        tags={"share"},
    ),
}

NAMES_GIRL = ["Mira", "Lina", "Elin", "Rose", "Anya", "Sera", "Talia"]
NAMES_BOY = ["Pip", "Owen", "Bram", "Jory", "Finn", "Emil", "Tobin"]
TRAITS = ["kind", "curious", "brave", "gentle", "careful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    treasure: str
    response: str
    child: str
    child_gender: str
    partner: str
    partner_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, treasure in TREASURES.items():
            if not reasonableness_ok(treasure, setting):
                continue
            for rid in RESPONSES:
                combos.append((sid, tid, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, partner, treasure, setting = f["child"], f["partner"], f["treasure_cfg"], f["setting"]
    return [
        f'Write a fairy-tale story for a young child that uses the word "aware" '
        f'and includes sharing, a lesson learned, and a twist.',
        f"Tell a story about {child.id} and {partner.id} at {setting.festival} who find {treasure.phrase} "
        f"and learn to share it.",
        f'Write a gentle fairy tale where a child is not only aware of a problem '
        f'but discovers that sharing opens up a magical surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, partner, treasure, setting = f["child"], f["partner"], f["treasure_cfg"], f["setting"]
    out: list[QAItem] = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {partner.id} in {setting.place}. They meet at {setting.festival} and discover {treasure.label}.",
        ),
        QAItem(
            question="Why was the partner aware something was wrong?",
            answer=f"{partner.id} was aware that keeping the treasure all to themselves would leave the other children with nothing. That small worry changed the mood and made the sharing choice important.",
        ),
    ]
    if f["outcome"] == "shared":
        out.append(QAItem(
            question="How did they solve the problem?",
            answer=f"They shared the {treasure.label}. That choice opened the way for the twist, because the treasure revealed {treasure.hidden_twist}.",
        ))
        out.append(QAItem(
            question="What lesson did the child learn?",
            answer=f"{child.id} learned that sharing can make a gift better instead of smaller. The surprise ending proved that kindness brought a bigger blessing to everyone.",
        ))
    else:
        out.append(QAItem(
            question="How did the story end?",
            answer=f"It ended before the treasure could truly open up, so the full twist did not happen. The story pauses on the lesson that sharing matters most when it is needed.",
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    treasure: Treasure = f["treasure_cfg"]
    if treasure.id == "bread":
        return [QAItem("What is honey bread?", "Honey bread is sweet bread flavored with honey. It is soft, tasty, and easy to share in slices.")]
    if treasure.id == "lantern":
        return [QAItem("What is a lantern?", "A lantern is a light that glows and helps people see in the dark. In fairy tales it often feels magical and gentle.")]
    return [QAItem("What are berries?", "Berries are small fruits that grow on plants. They can be sweet, juicy, and nice to share.")]


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, treasure: Treasure) -> str:
    return f"(No story: {setting.place} and {treasure.label} do not make a plausible fairy-tale sharing twist.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(x.id for x in sensible_responses())
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense}). Try: {better}.)"


ASP_RULES = r"""
shareable(T) :- treasure(T), tag(T, shareable).
valid(S, T, R) :- setting(S), treasure(T), response(R), shareable(T), fairy(S).
twist_seen :- opened(gift).
outcome(shared) :- shared_once, twist_seen.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "fairy" in s.tags:
            lines.append(asp.fact("fairy", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: aware, sharing, lesson learned, twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if args.treasure and args.setting:
        if not reasonableness_ok(TREASURES[args.treasure], SETTINGS[args.setting]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], TREASURES[args.treasure]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treasure, response = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    child = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    partner = args.partner or rng.choice(NAMES_BOY if gender == "girl" else NAMES_GIRL)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(setting, treasure, response, child, gender, partner, "girl" if gender == "boy" else "boy", rng.choice(TRAITS), delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TREASURES[params.treasure], RESPONSES[params.response],
                 params.child, params.child_gender, params.partner, params.partner_gender, params.delay)
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


CURATED = [
    StoryParams("meadow", "bread", "gentle", "Mira", "girl", "Pip", "boy", "kind", 0),
    StoryParams("castle", "lantern", "song", "Lina", "girl", "Owen", "boy", "careful", 0),
    StoryParams("village", "berries", "gentle", "Tobin", "boy", "Rose", "girl", "brave", 1),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
