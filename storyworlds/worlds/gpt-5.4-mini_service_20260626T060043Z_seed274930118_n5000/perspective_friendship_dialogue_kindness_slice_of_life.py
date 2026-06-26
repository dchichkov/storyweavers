#!/usr/bin/env python3
"""
storyworlds/worlds/perspective_friendship_dialogue_kindness_slice_of_life.py
============================================================================

A small slice-of-life story world about perspective, friendship, dialogue, and
kindness.

Seed tale used to build the model:
---
On a quiet afternoon, Jun saw his friend Mira sitting alone on the library steps
with her lunch untouched. She looked upset, so Jun almost walked away, thinking
she wanted to be left alone. Then he noticed a crumpled note in her hand and
asked gently what was wrong. Mira explained that she had been embarrassed after
forgetting her reading card, and she was worried the librarian would be annoyed.

Jun listened, offered to help, and shared his sandwich. Mira smiled, thanked him,
and said she felt better just having someone listen. Together they went back
inside, and Jun understood that sometimes a friend's quiet face meant worry, not
anger.

Causal shape:
---
- uncertain reading of a friend  -> doubt, distance, concern
- gentle question                -> truth becomes visible
- kindness + shared help         -> closeness, relief, friendship grows
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["clean", "shared", "helpful"]:
            self.meters.setdefault(k, 0.0)
        for k in ["warmth", "worry", "relief", "friendship", "kindness", "distance", "curiosity"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    time: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    label: str
    phrase: str
    type: str
    kind: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    setting: str
    item: str
    name: str
    friend_name: str
    gender: str
    friend_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "library_steps": Setting(place="the library steps", time="afternoon", affords={"talk", "share", "sit"}),
    "bench": Setting(place="the neighborhood bench", time="evening", affords={"talk", "share", "sit"}),
    "kitchen_table": Setting(place="the kitchen table", time="morning", affords={"talk", "share", "sit"}),
    "playground_bench": Setting(place="the playground bench", time="after school", affords={"talk", "share", "sit"}),
}

ITEMS = {
    "sandwich": Item(label="sandwich", phrase="a sandwich wrapped in wax paper", type="sandwich", kind="food"),
    "book_card": Item(label="library card", phrase="a small library card", type="card", kind="paper"),
    "juice_box": Item(label="juice box", phrase="a little juice box", type="juice box", kind="food"),
    "cookie_box": Item(label="cookie box", phrase="a box of homemade cookies", type="cookies", kind="food", plural=True),
}

NAMES = {
    "girl": ["Mira", "Lena", "Ivy", "Noor", "Sofia"],
    "boy": ["Jun", "Eli", "Noah", "Owen", "Theo"],
}

FRIEND_NAMES = {
    "girl": ["Mina", "Ari", "Pia", "Sana", "Rae"],
    "boy": ["Kai", "Finn", "Leo", "Ben", "Milo"],
}


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            if "share" in setting.affords:
                out.append((sid, iid))
    return out


def reasonableness_gate(setting: str, item: str) -> None:
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if item not in ITEMS:
        raise StoryError("Unknown item.")
    if (setting, item) not in valid_combos():
        raise StoryError("This setting and item do not fit a believable slice-of-life friendship scene.")


def introduce(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a gentle {hero.type} who noticed the small moods in a room. "
        f"{friend.id} was {hero.pronoun('possessive')} friend, and {item.phrase} was waiting nearby."
    )


def setup_scene(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    item.meters["shared"] += 1
    world.say(
        f"One {world.setting.time}, {hero.id} and {friend.id} met at {world.setting.place}. "
        f"{friend.id} sat very still, looking down at {friend.pronoun('possessive')} hands."
    )
    world.say(
        f"{hero.id} noticed {friend.id} had not touched {friend.pronoun('possessive')} {item.label}."
    )


def misread(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["distance"] += 1
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} thought, 'Maybe {friend.id} wants to be alone.' "
        f"{hero.id} almost stayed quiet, because {hero.pronoun('subject')} did not want to bother a friend."
    )


def ask_gently(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then {hero.id} took a breath and asked, 'Are you okay?' "
        f"The question was soft enough to feel kind, not nosy."
    )
    friend.memes["curiosity"] += 1


def reveal(world: World, friend: Entity, item: Entity) -> None:
    friend.memes["worry"] = 0.0
    friend.memes["relief"] += 1
    friend.memes["warmth"] += 1
    friend.meters["clean"] += 0.5
    world.say(
        f"{friend.id} looked up and said, 'I am not mad. I just forgot {friend.pronoun('possessive')} {item.label}, "
        f"and I was scared someone would be upset.'"
    )
    world.say(
        f"{friend.id} held up {friend.pronoun('possessive')} {item.label} and gave a small, embarrassed smile."
    )


def kindness(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["warmth"] += 1
    hero.memes["distance"] = 0.0
    hero.memes["worry"] = 0.0
    friend.memes["friendship"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} smiled back and said, 'We can fix that together.' "
        f"{hero.id} shared {hero.pronoun('possessive')} snack and offered to help."
    )
    if item.type == "card":
        world.say(
            f"They walked inside together, and {hero.id} waited with {friend.id} while the librarian looked for the card record."
        )
    else:
        world.say(
            f"{hero.id} slid {hero.pronoun('possessive')} own food across the table so {friend.id} would not sit hungry."
        )


def ending(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["friendship"] += 1
    hero.memes["relief"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"In the end, {friend.id}'s shoulders loosened, and the two friends sat closer together. "
        f"What first looked like a cold face had really been a worried one."
    )
    world.say(
        f"{hero.id} learned that a quiet expression can mean many things, and kindness can help a friend feel seen."
    )


def tell(setting: Setting, item_cfg: Item, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, label=friend_name))
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, plural=item_cfg.plural))

    introduce(world, hero, friend, item)
    world.para()
    setup_scene(world, hero, friend, item)
    misread(world, hero, friend)
    ask_gently(world, hero, friend)
    reveal(world, friend, item)
    world.para()
    kindness(world, hero, friend, item)
    ending(world, hero, friend, item)

    world.facts.update(hero=hero, friend=friend, item=item, setting=setting, item_cfg=item_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    return [
        f'Write a short slice-of-life story about {hero.id} and {friend.id} at {world.setting.place} with the theme "perspective."',
        f"Tell a gentle friendship story where {hero.id} thinks {friend.id} feels one way, then asks kindly and learns the truth.",
        f'Write a child-friendly story about sharing, dialogue, and kindness that includes a {item.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item = f["hero"], f["friend"], f["item_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.id} first think {friend.id} was upset?",
            answer=f"{hero.id} saw {friend.id} sitting quiet at {world.setting.place}, so {hero.pronoun('subject')} guessed {friend.id} wanted to be left alone.",
        ),
        QAItem(
            question=f"What did {hero.id} do to check on {friend.id}?",
            answer=f"{hero.id} asked gently, 'Are you okay?' instead of walking away.",
        ),
        QAItem(
            question=f"What was really wrong with {friend.id}?",
            answer=f"{friend.id} had forgotten {friend.pronoun('possessive')} {item.label} and felt embarrassed and worried.",
        ),
        QAItem(
            question=f"How did {hero.id} show kindness?",
            answer=f"{hero.id} listened, shared {hero.pronoun('possessive')} snack, and stayed with {friend.id} until things felt better.",
        ),
        QAItem(
            question=f"What did the two friends learn in the end?",
            answer=f"They learned that a quiet face does not always mean anger, and that a kind question can change a whole moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is perspective?",
            answer="Perspective means the way someone sees or understands a situation from their own point of view.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="A dialogue is a conversation where people talk and listen to each other.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring relationship between people who trust and help each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library_steps", item="book_card", name="Jun", friend_name="Mira", gender="boy", friend_gender="girl"),
    StoryParams(setting="bench", item="sandwich", name="Lena", friend_name="Kai", gender="girl", friend_gender="boy"),
    StoryParams(setting="kitchen_table", item="juice_box", name="Owen", friend_name="Pia", gender="boy", friend_gender="girl"),
]


ASP_RULES = r"""
% A scene is reasonable when a setting can host a quiet talking/sharing moment.
scene(S, I) :- setting(S), item(I), affords(S, share).

% The friend can be helped when there is an item to share and the scene supports it.
helpful(S, I) :- scene(S, I).

#show scene/2.
#show helpful/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show scene/2."))
    return sorted(set(asp.atoms(model, "scene")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    python_set = {(s, i) for s, i in python_set}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life friendship story world about perspective, dialogue, and kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.setting and args.item:
        reasonableness_gate(args.setting, args.item)

    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if not combos:
        raise StoryError("No valid story matches those options.")

    setting, item = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(NAMES[hero_gender])
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES[friend_gender])

    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES[friend_gender] if n != hero_name])

    item_cfg = ITEMS[item]
    if hero_gender not in item_cfg.genders:
        raise StoryError("That item does not fit the chosen hero gender in this world.")

    return StoryParams(
        setting=setting,
        item=item,
        name=hero_name,
        friend_name=friend_name,
        gender=hero_gender,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        params.name,
        params.gender,
        params.friend_name,
        params.friend_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show scene/2.\n#show helpful/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show scene/2.\n#show helpful/2."))
        scenes = sorted(set(asp.atoms(model, "scene")))
        helpful = sorted(set(asp.atoms(model, "helpful")))
        print(f"{len(scenes)} scenes; {len(helpful)} helpful combinations:\n")
        for s in scenes:
            print(f"  {s[0]:18} {s[1]:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.setting} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
