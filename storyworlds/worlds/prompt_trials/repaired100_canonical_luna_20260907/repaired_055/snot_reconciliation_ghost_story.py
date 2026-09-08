#!/usr/bin/env python3
"""
A small ghost-story world about snot, reconciliation, and a friendship repaired
in an old house.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Incident:
    room: str
    object_name: str
    ghost_name: str
    mistake: str
    consequence: str
    clue: str
    ghost_line: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    child_name: str = "Luna"
    friend_name: str = "Mara"
    ghost_name: str = "Pip"
    room: str = "attic"
    trait: str = "brave"
    seed: Optional[int] = None


INCIDENTS = [
    Incident(
        room="the dusty attic",
        object_name="an old silver mirror",
        ghost_name="Pip",
        mistake="wiped a blob of snot from the mirror and called the hidden ghost a thief",
        consequence="the mirror went dark, and a cold wind scattered the friendship bracelets on the floor",
        clue="the snot was on the mirror's outside edge, exactly where a frightened nose might have touched it",
        ghost_line="I did not steal your bracelet. I hid it because I was lonely and hoped someone would stay.",
        repair="apologized for shouting, cleaned the mirror gently, and shared the bracelet with the ghost",
        lesson="a scary-looking mess may hide a lonely feeling, and an honest apology can open a door",
        ending="the mirror shone again, showing three smiling faces and one little ghostly nose",
    ),
    Incident(
        room="the narrow upstairs hall",
        object_name="a crooked coat hook",
        ghost_name="Pip",
        mistake="left a snotty handkerchief on the hook and blamed the ghost when it vanished",
        consequence="the hallway filled with soft sobs, and every door creaked open at once",
        clue="a trail of tiny damp fingerprints led beneath the oldest door",
        ghost_line="I carried the handkerchief away because its smell reminded me of home.",
        repair="found the handkerchief, admitted the unfair accusation, and offered a clean one",
        lesson="listening before blaming gives a hurt friend room to tell the truth",
        ending="the doors settled quietly while two fresh handkerchiefs hung side by side",
    ),
    Incident(
        room="the moonlit kitchen",
        object_name="a blue soup bowl",
        ghost_name="Pip",
        mistake="sneezed snot onto the bowl and accused the ghost of making it float",
        consequence="the bowl circled the ceiling, splashing cold soup over the family table",
        clue="a small ghostly hand was holding the bowl steady, not pushing it",
        ghost_line="I was trying to carry dinner to you. Ghosts cannot always hold things the usual way.",
        repair="said sorry, washed the bowl, and carried the soup together one careful step at a time",
        lesson="reconciliation begins when someone replaces a quick accusation with a patient question",
        ending="the blue bowl rested on the table, and its soup steamed beneath a friendly moon",
    ),
    Incident(
        room="the quiet music room",
        object_name="a cracked toy piano",
        ghost_name="Pip",
        mistake="sniffled snot onto the keys and said the ghost had played the sour notes",
        consequence="the piano repeated one sad chord until the windows trembled",
        clue="the lowest key was pressed by a transparent finger while the other keys stayed still",
        ghost_line="That sad chord is the song I played when my best friend stopped speaking to me.",
        repair="confessed the mistake, listened to the whole song, and played a bright ending beside the ghost",
        lesson="sharing hurt honestly can turn a quarrel into a chance to make music together",
        ending="the cracked piano played one warm chord, and the ghost's humming joined it",
    ),
]


TRAITS = ["brave", "curious", "careful", "kind", "thoughtful"]
NAMES = ["Luna", "Mara", "Nia", "Theo", "Ivy", "Owen"]


def reasonable(params: StoryParams) -> bool:
    return (
        bool(params.child_name)
        and bool(params.friend_name)
        and params.child_name != params.friend_name
        and params.room == "attic"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story about snot and reconciliation.")
    ap.add_argument("--child-name", default=None)
    ap.add_argument("--friend-name", default=None)
    ap.add_argument("--ghost-name", default=None)
    ap.add_argument("--room", choices=["attic"], default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child_name or rng.choice(NAMES)
    possible = [n for n in NAMES if n != child]
    friend = args.friend_name or rng.choice(possible)
    ghost = args.ghost_name or "Pip"
    if child == friend:
        raise StoryError("The two living friends must have different names.")
    return StoryParams(
        child_name=child,
        friend_name=friend,
        ghost_name=ghost,
        room=args.room or "attic",
        trait=rng.choice(TRAITS),
    )


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child_name, "character", "child"))
    friend = world.add(Entity(params.friend_name, "character", "friend"))
    ghost = world.add(Entity(params.ghost_name, "character", "ghost"))
    incident = INCIDENTS[(params.seed or 0) % len(INCIDENTS)]

    world.say(f"{params.trait.capitalize()} {child.id} climbed into {incident.room} with {friend.id}.")
    world.say(f"They had come to examine {incident.object_name}, which glimmered beneath a sheet of moonlight.")
    world.say(f'Near it, {child.id} sneezed and cried, "Achoo!" A little bit of snot landed where they could both see it.')
    world.say(f"At that very moment, {incident.ghost_name} appeared as a pale shape in the glass.")
    world.say(f"{child.id} {incident.mistake}.")
    add_meme(child, "fear", 1)
    add_meme(friend, "doubt", 1)
    add_meter(child, "distance", 1)
    world.para()

    world.say(f"{incident.consequence}.")
    world.say(f"{friend.id} whispered, 'Wait. What makes you think {incident.ghost_name} did it?'")
    world.say(f"{child.id} answered, 'I saw the ghost when the trouble began.'")
    world.say(f"{friend.id} pointed out that {incident.clue}.")
    world.say(f"Together they looked again, and the frightening moment began to make sense.")
    world.para()

    add_meme(ghost, "loneliness", 1)
    add_meme(friend, "kindness", 1)
    add_meme(child, "understanding", 1)
    world.say(f'{incident.ghost_name} spoke in a thin, trembling voice: "{incident.ghost_line}"')
    world.say(f"{child.id} lowered their eyes and said, 'I am sorry I blamed you. Will you let us help?'")
    world.say(f"{incident.ghost_name} nodded, and {friend.id} added, 'We can fix this together.'")
    world.say(f"The friends {incident.repair}.")
    add_meter(child, "care", 1)
    add_meter(friend, "support", 1)
    add_meme(child, "relief", 1)
    add_meme(ghost, "trust", 1)
    world.para()

    world.say(f"They learned that {incident.lesson}.")
    world.say(f"{incident.ending}.")
    world.say(f"After that night, {child.id}, {friend.id}, and {incident.ghost_name} visited the old house together whenever someone needed a friend.")

    world.facts.update(
        child=child,
        friend=friend,
        ghost=ghost,
        incident=incident,
        resolved=True,
        reconciliation=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    return [
        f"Write a child-friendly ghost story in {incident.room} about {child.id}, snot, and reconciliation.",
        f"Show {child.id} misunderstanding {ghost.id}, then discovering evidence and repairing the hurt.",
        f"End with a concrete image proving that the ghost and the children are friends again: {incident.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    ghost = world.facts["ghost"]
    incident = world.facts["incident"]
    return [
        QAItem(
            f"What did {child.id} wrongly blame {ghost.id} for?",
            f"{child.id} blamed {ghost.id} for {incident.mistake}. The child judged the ghost before checking the evidence.",
        ),
        QAItem(
            f"What clue helped {friend.id} question the accusation?",
            f"{friend.id} noticed that {incident.clue}. That clue showed that the first explanation might be wrong.",
        ),
        QAItem(
            f"How did the children reconcile with {ghost.id}?",
            f"They apologized, listened to the ghost's feelings, and {incident.repair}. Their actions rebuilt trust.",
        ),
        QAItem(
            "What did the characters learn?",
            f"They learned that {incident.lesson}.",
        ),
        QAItem(
            "What final image showed that the reconciliation worked?",
            f"{incident.ending}. The shared image showed that fear had changed into friendship.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a ghost story?",
            "A ghost story is a tale about a spirit or mysterious presence, often using gentle suspense to explore feelings, choices, or friendship.",
        ),
        QAItem(
            "What does reconciliation mean?",
            "Reconciliation means repairing a relationship after hurt or disagreement by telling the truth, listening, apologizing, and choosing trust again.",
        ),
        QAItem(
            "Why should someone check evidence before blaming another person?",
            "Checking evidence matters because a frightening guess can be wrong, while careful attention can reveal what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
character(C) :- child(C).
character(F) :- friend(F).
character(G) :- ghost(G).
misunderstanding(C,G) :- child(C), ghost(G), blamed(C,G).
evidence_checked(C,F) :- child(C), friend(F), clue_found(F).
apology(C,G) :- child(C), ghost(G), says_sorry(C,G).
reconciliation(C,G) :- misunderstanding(C,G), evidence_checked(C,_), apology(C,G), repaired(C,G).
resolved(C,G) :- reconciliation(C,G).
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child", "luna"),
            asp.fact("friend", "mara"),
            asp.fact("ghost", "pip"),
            asp.fact("blamed", "luna", "pip"),
            asp.fact("clue_found", "mara"),
            asp.fact("says_sorry", "luna", "pip"),
            asp.fact("repaired", "luna", "pip"),
        ]
    )


def asp_program(show: str = "#show resolved/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    result = bool(asp.atoms(model, "resolved"))
    if result:
        print("OK: ASP and Python reconciliation agree.")
        return 0
    print("MISMATCH between ASP and Python reconciliation.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:8} ({entity.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Mara", "Pip", "attic", "brave"),
        StoryParams("Theo", "Ivy", "Pip", "attic", "curious"),
        StoryParams("Nia", "Owen", "Pip", "attic", "careful"),
        StoryParams("Mara", "Luna", "Pip", "attic", "kind"),
    ]


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError("This storyworld requires two different names and the old attic.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(valid_story_params()):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n) * 30):
            if len(samples) >= max(1, args.n):
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} and {sample.params.friend_name} in the haunted attic"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
