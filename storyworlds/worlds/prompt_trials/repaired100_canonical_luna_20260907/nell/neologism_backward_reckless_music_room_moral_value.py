#!/usr/bin/env python3
"""A fairy-tale music-room world about a reckless word and the value of sharing."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


NAMES = ("Luna", "Mira", "Tess", "Nell")
INSTRUMENTS = ("lute", "violin", "flute")
MORALS = ("sharing", "patience")
VOICES = ("gentle", "bright", "plain")
MAX_ACTIONS = 16


@dataclass
class StoryParams:
    hero: str = "Luna"
    instrument: str = "lute"
    moral: str = "sharing"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str = "music_room"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    fact_events: dict[str, int] = field(default_factory=dict)
    outcome: str = ""

    def snapshot(self):
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.fact_events]
        if missing:
            raise StoryError(f"{kind} needs missing evidence: {', '.join(missing)}.")
        event_id = len(self.history)
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        self.history.append(
            Event(event_id, kind, actor, data, tuple(facts), causes, self.snapshot())
        )
        for fact in facts:
            self.fact_events[fact] = event_id


def validate_params(p: StoryParams):
    if p.hero not in NAMES:
        raise StoryError(f"Unknown hero {p.hero!r}.")
    if p.instrument not in INSTRUMENTS:
        raise StoryError(f"Unknown instrument {p.instrument!r}.")
    if p.moral not in MORALS:
        raise StoryError(f"Unknown moral {p.moral!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice {p.voice!r}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    entities = {
        "luna": Entity("luna", p.hero, "character", memes={"curiosity": 1, "kindness": .5}),
        "pip": Entity("pip", "Pip the little fiddler", "character",
                      memes={"fear": .8, "hope": .2}),
        "bell": Entity("bell", "the silver bell", "character",
                       memes={"mischief": 1}, beliefs={"word": "plim"}),
        "instrument": Entity(
            "instrument", f"the {p.instrument}", "instrument",
            meters={"voices": 1, "shared": 0, "tuned": 1},
            memes={"pride": 1},
        ),
        "music_room": Entity(
            "music_room", "the music room", "place",
            meters={"doors": 1, "echo": 1, "chairs": 2},
        ),
        "memory": Entity("memory", "the old memory", "memory"),
    }
    w = World(p, entities)
    w.record(
        "opening",
        "bell",
        facts=("bell_speaks", "room_known"),
        hero=p.hero,
        instrument=p.instrument,
        word="plim",
    )
    return w


def choose_action(w: World) -> str:
    if "ending" in w.fact_events:
        return "close"
    if "flashback" not in w.fact_events:
        return "remember"
    if "meaning_known" not in w.fact_events:
        return "ask_meaning"
    if "reckless_turn" not in w.fact_events:
        return "reckless_play"
    if "sharing_decided" not in w.fact_events:
        return "choose_share"
    if "music_shared" not in w.fact_events:
        return "share_music"
    return "close"


def execute(w: World, action: str):
    p = w.params
    if action == "remember":
        w.entities["luna"].beliefs["past"] = "Pip once played alone and was laughed at."
        w.entities["luna"].memes["kindness"] = 1
        w.record(
            "remember",
            "luna",
            facts=("flashback",),
            needs=("bell_speaks",),
            memory="Pip once played alone and was laughed at.",
        )
    elif action == "ask_meaning":
        w.entities["luna"].beliefs["meaning"] = "plim means share the song"
        w.entities["bell"].beliefs["meaning"] = "share the song"
        w.record(
            "ask_meaning",
            "luna",
            facts=("meaning_known",),
            needs=("flashback",),
            word="plim",
            meaning="share the song",
        )
    elif action == "reckless_play":
        inst = w.entities["instrument"]
        inst.meters["tuned"] = 0
        inst.memes["pride"] = .1
        w.entities["bell"].memes["mischief"] = .2
        w.record(
            "reckless_play",
            "bell",
            facts=("reckless_turn", "instrument_sour"),
            needs=("meaning_known",),
            word="plim",
        )
    elif action == "choose_share":
        w.entities["luna"].beliefs["choice"] = "invite Pip"
        w.entities["pip"].beliefs["welcome"] = "yes"
        w.entities["luna"].memes["kindness"] = 1
        w.record(
            "choose_share",
            "luna",
            facts=("sharing_decided",),
            needs=("reckless_turn", "flashback"),
        )
    elif action == "share_music":
        inst = w.entities["instrument"]
        inst.meters["tuned"] = 1
        inst.meters["shared"] = 1
        w.entities["pip"].memes["fear"] = 0
        w.entities["pip"].memes["hope"] = 1
        w.entities["bell"].memes["mischief"] = 0
        w.outcome = "shared_song"
        w.record(
            "share_music",
            "luna",
            facts=("music_shared", "conflict_resolved"),
            needs=("sharing_decided", "instrument_sour"),
        )
    elif action == "close":
        if not w.outcome:
            raise StoryError("The music room has no resolution.")
        w.record("close", "luna", facts=("ending",), needs=("conflict_resolved",))
    else:
        raise StoryError(f"Unknown action {action!r}.")


def validate_world(w: World):
    if w.outcome != "shared_song" or "ending" not in w.fact_events:
        raise StoryError("The story must end with a shared song.")
    if w.entities["instrument"].meters["shared"] != 1:
        raise StoryError("The instrument was not shared.")
    if w.entities["pip"].memes["fear"] != 0:
        raise StoryError("Pip is still afraid at the ending.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event depends on a future event.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.fact_events:
            validate_world(w)
            return w
    raise StoryError("The music-room tale did not resolve.")


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.parts = []
        self.qa = []
        self.context = {
            "hero": self.p.hero,
            "instrument": self.p.instrument,
            "word": "plim",
        }

    def add(self, *choices):
        self.parts.append(self.rng.choice(choices).format(**self.context))

    def dialogue(self, lines):
        for speaker, line in lines:
            name = self.context["hero"] if speaker == "luna" else "Pip" if speaker == "pip" else "the bell"
            verb = "asked" if line.endswith("?") else "said"
            self.parts.append(f'"{line}" {name} {verb}.')

    def render(self):
        for event in self.world.history:
            k = event.kind
            if k == "opening":
                self.add(
                    "In the music room, where moonlight slept on every instrument, a silver bell began to speak.",
                    "One evening, the music room was quiet until the silver bell rang without being touched.",
                )
                self.dialogue((
                    ("bell", "Plim!"),
                    ("luna", "Is that a word, or only a noise?"),
                    ("bell", "It is a word waiting for a kind heart."),
                ))
                self.add(
                    f"The bell pointed its tongue toward the {self.p.instrument}. Pip the little fiddler stood beside it, holding his bow very still."
                )
                self.qa.append(QAItem(
                    "Where did the bell speak?",
                    "The bell spoke in the music room beside the " + self.p.instrument + ".",
                ))
            elif k == "remember":
                self.add(
                    "Then Luna remembered a winter afternoon. Pip had played one brave note alone, and the other children had laughed.",
                    "A flashback came to Luna: Pip's first song had trembled through the room while unkind laughter chased it away.",
                )
                self.dialogue((
                    ("luna", "No one should be left alone with a song."),
                    ("pip", "I thought you had forgotten."),
                    ("luna", "A true friend remembers what hurts."),
                ))
                self.qa.append(QAItem(
                    "What did Luna remember?",
                    "She remembered that Pip had once played alone and been laughed at.",
                ))
            elif k == "ask_meaning":
                self.dialogue((
                    ("luna", "What does plim mean?"),
                    ("bell", "It means share the song."),
                    ("luna", "Then we must share it wisely."),
                ))
                self.add(
                    "The strange word was a neologism, a new word made for a new kindness. Luna understood that its meaning was larger than its tiny sound."
                )
                self.qa.append(QAItem(
                    "What did the neologism plim mean?",
                    "Plim meant that the song should be shared with someone else.",
                ))
            elif k == "reckless_play":
                self.add(
                    "The bell grew reckless and struck the strings backward, from ending to beginning. The music came out sour and strange.",
                    "With a reckless clang, the bell sent the melody backward. The last note came first, and the room filled with crooked music.",
                )
                self.dialogue((
                    ("pip", "That sound makes my ears hide."),
                    ("luna", "Stop, bell. A new word is not permission to hurt."),
                    ("bell", "I only wanted everyone to notice me."),
                ))
                self.qa.append(QAItem(
                    "Why did the bell's music fail?",
                    "The bell played recklessly and backward, so the notes became sour and confused.",
                ))
            elif k == "choose_share":
                self.add(
                    "Luna did not scold the bell. She remembered Pip's lonely afternoon and chose the moral value of sharing.",
                    "Because of her flashback, Luna chose kindness instead of blame. She invited Pip to make the song with her.",
                )
                self.dialogue((
                    ("luna", "Pip, will you play the first note with me?"),
                    ("pip", "Even if my hands shake?"),
                    ("luna", "Especially then."),
                ))
            elif k == "share_music":
                self.add(
                    "Luna tuned the instrument, Pip held the melody, and the bell kept a gentle beat. The music no longer ran backward; it traveled forward from one friend to another.",
                    "Together they repaired the sour sound. Pip played a small clear note, Luna answered it, and the bell learned to listen before ringing.",
                )
                self.dialogue((
                    ("bell", "Plim."),
                    ("pip", "Now I know what it means."),
                    ("luna", "A song grows brighter when more than one heart carries it."),
                ))
                self.qa.append(QAItem(
                    "How did Luna solve the music-room trouble?",
                    "She invited Pip to share the instrument and helped the bell play gently, so their music moved forward together.",
                ))
            elif k == "close":
                self.add(
                    "That night, the music room kept their song like a warm secret. The little word plim shone in the bell, and no player stood alone.",
                    "From then on, every song in the room began with an invitation. The bell remembered that sharing was a better treasure than being heard alone.",
                )
                self.qa.append(QAItem(
                    "What changed at the end?",
                    "The musicians shared the song, Pip gained courage, and the bell learned that sharing mattered more than attention.",
                ))
        return "\n\n".join(self.parts)


ASP_RULES = """
valid_word(plim).
meaning(plim,sharing).
safe_play(share).
safe_play(listen).
requires_flashback(share).
resolves(share,shared_song).
#show valid_word/1.
#show meaning/2.
#show safe_play/1.
#show requires_flashback/1.
#show resolves/2.
"""


def asp_facts():
    from asp import fact
    return "\n".join([
        fact("valid_word", "plim"),
        fact("meaning", "plim", "sharing"),
        fact("safe_play", "share"),
        fact("safe_play", "listen"),
        fact("requires_flashback", "share"),
        fact("resolves", "share", "shared_song"),
    ])


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story = Teller(world).render()
    return StorySample(
        params=p,
        story=story,
        prompts=[
            f"Write a fairy tale about {p.hero} in a music room, where a new word teaches the value of sharing."
        ],
        story_qa=Teller(world).qa,
        world_qa=[
            QAItem(
                "What is a moral value in this world?",
                "Sharing is a moral value because music becomes kinder when everyone can take part.",
            ),
            QAItem(
                "What is a flashback?",
                "A flashback is a return to an earlier memory that helps a character understand the present.",
            ),
        ],
        world=world,
    )


def verify():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    if set(atoms(model, "valid_word")) != {("plim",)}:
        raise StoryError("ASP disagrees about the new word.")
    if set(atoms(model, "meaning")) != {("plim", "sharing")}:
        raise StoryError("ASP disagrees about the word's meaning.")
    for seed in range(12):
        p = StoryParams(world_seed=seed, prose_seed=seed)
        sample = generate(p)
        if "sharing" not in sample.story.lower() and "share" not in sample.story.lower():
            raise StoryError("Generated story omitted sharing.")
        if "backward" not in sample.story.lower():
            raise StoryError("Generated story omitted backward.")
        if "reckless" not in sample.story.lower():
            raise StoryError("Generated story omitted reckless.")
    print("OK: Python simulation, prose, and ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--instrument", choices=INSTRUMENTS)
    parser.add_argument("--moral", choices=MORALS)
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        voice=args.voice,
    )
    for name, choices in (
        ("hero", NAMES),
        ("instrument", INSTRUMENTS),
        ("moral", MORALS),
    ):
        value = getattr(args, name)
        setattr(p, name, value if value is not None else rng.choice(choices) if sample else getattr(p, name))
    validate_params(p)
    return p


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "state": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            from asp import atoms, one_model
            model = one_model(asp_facts() + "\n" + ASP_RULES)
            print(json.dumps({
                "valid_word": atoms(model, "valid_word"),
                "meaning": atoms(model, "meaning"),
                "safe_play": atoms(model, "safe_play"),
                "resolves": atoms(model, "resolves"),
            }))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                resolve_params(args, rng, i, sample=False)
                for i in range(len(INSTRUMENTS))
            ]
            for i, instrument in enumerate(INSTRUMENTS):
                params[i].instrument = instrument
        else:
            params = [
                resolve_params(args, rng, i, sample=args.n > 1)
                for i in range(args.n)
            ]
        samples = [generate(p) for p in params]
        if args.json:
            rows = [sample.to_dict() for sample in samples]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
