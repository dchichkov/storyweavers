"""A small deterministic beat director; no repository or third-party imports."""
from copy import deepcopy
from dataclasses import dataclass
import json
import random
import re


def read(state, path):
    value = state
    for part in path.split("."):
        value = value[part]
    return value


def matches(state, conditions):
    for path, op, expected in conditions:
        actual = read(state, path)
        if not {"eq": lambda: actual == expected,
                "ge": lambda: actual >= expected,
                "le": lambda: actual <= expected,
                "lt": lambda: actual < expected,
                "gt": lambda: actual > expected}[op]():
            return False
    return True


def apply(state, effects):
    """All prose is paired with explicit effects on physical carriers or control state."""
    for op, path, value in effects:
        owner = state
        parts = path.split(".")
        for part in parts[:-1]:
            owner = owner[part]
        key = parts[-1]
        if op == "set":
            owner[key] = value
        elif op == "add":
            owner[key] = max(0, min(10, owner[key] + value))
        else:
            raise ValueError("Unknown effect: " + op)


@dataclass(frozen=True)
class Performance:
    id: str
    lines: tuple
    effects: tuple = ()
    when: tuple = ()


@dataclass(frozen=True)
class Goal:
    id: str
    variants: tuple


@dataclass(frozen=True)
class Beat:
    id: str
    phase: str
    topic: str
    tension: float
    goals: tuple
    priority: int = 0
    weight: float = 1.0
    when: tuple = ()
    resume: str = "The conversation returns to where it broke off."


@dataclass(frozen=True)
class Exchange:
    id: str
    label: str
    variants: tuple
    # Influence rules decide willingness; effects belong to the resulting performance.
    influences: tuple = ()
    threshold: int = 0


class Session:
    def __init__(self, seed=0):
        from content import BEATS, EXCHANGES, INITIAL, MIXINS, ENDINGS
        self.beats = {b.id: b for b in BEATS}
        self.exchanges = EXCHANGES
        self.mixins = MIXINS
        self.endings = ENDINGS
        self.state = deepcopy(INITIAL)
        self.seed = seed
        self.rng = random.Random(seed)
        self.active = None
        self.cursor = 0
        self.interrupted = False
        self.completed = []
        self.aborted = []
        self.used_exchanges = set()
        self.topic_tiers = {topic: 0 for topic in MIXINS}
        self.focus = ""
        self.commands = []
        self.events = []
        self.selections = []
        self.transcript = []
        self.outcome = None
        self.started = False

    @property
    def tension(self):
        chars = self.state["people"]
        return sum(chars[n]["memes"]["anger"] + chars[n]["memes"]["fear"]
                   for n in ("mara", "eli")) / 4

    def snapshot(self):
        return deepcopy(self.state)

    def emit(self, performance, kind, source):
        before = self.snapshot()
        apply(self.state, performance.effects)
        lines = list(performance.lines)
        self.transcript.extend(lines)
        self.events.append({"id": len(self.events), "turn": self.state["turn"],
                            "kind": kind, "source": source, "variant": performance.id,
                            "before": before, "after": self.snapshot(), "lines": lines})
        return lines

    def perform(self, variants, kind, source):
        for variant in variants:
            if matches(self.state, variant.when):
                return self.emit(variant, kind, source)
        raise ValueError("No compatible performance for " + source)

    def phase(self):
        if "arrival" not in self.completed:
            return "arrival"
        player = self.state["people"]["player"]
        if player["requested_space"] or player["requested_talk"]:
            return "decision"
        if "reckoning" in self.completed:
            return "decision"
        topic_count = sum(self.beats[b].phase == "topics" for b in self.completed)
        if topic_count >= 2 or self.state["turn"] >= 10:
            return "crisis"
        return "topics"

    def select_beat(self):
        phase = self.phase()
        target = {"arrival": 2, "topics": 4, "crisis": 6, "decision": 3}[phase]
        candidates = []
        for beat in self.beats.values():
            if (beat.phase != phase or beat.id in self.completed
                    or not matches(self.state, beat.when)):
                continue
            # Priority dominates; topic relevance and tension fit rank within it.
            score = (100 * beat.priority + beat.weight
                     + (4 if self.focus == beat.topic else 0)
                     - abs(beat.tension - target)
                     - 0.25 * abs(beat.tension - self.tension))
            candidates.append((score, beat))
        if not candidates:
            raise RuntimeError("No eligible beat in phase " + phase)
        best = max(score for score, _ in candidates)
        tied = [beat for score, beat in candidates if score == best]
        chosen = self.rng.choice(tied)
        self.selections.append({"turn": self.state["turn"], "phase": phase,
                                "target_tension": target, "current_tension": self.tension,
                                "focus": self.focus,
                                "candidates": [{"beat": b.id, "score": round(s, 3)}
                                               for s, b in candidates],
                                "chosen": chosen.id})
        self.active, self.cursor = chosen.id, 0

    def advance(self):
        if self.active is None:
            self.select_beat()
        beat = self.beats[self.active]
        lines = []
        if self.interrupted:
            lines += self.emit(Performance("resume", (beat.resume,)), "resume", beat.id)
            self.interrupted = False
        goal = beat.goals[self.cursor]
        lines += self.perform(goal.variants, "goal", beat.id + "." + goal.id)
        self.cursor += 1
        if self.cursor == len(beat.goals):
            self.completed.append(beat.id)
            self.active, self.cursor = None, 0
            if beat.phase == "decision":
                lines += self.finish()
        return lines

    def start(self):
        if self.started:
            return []
        self.started = True
        return self.advance()

    def finish(self, forced=None):
        if self.outcome:
            return []
        for name, variants, conditions in self.endings:
            if (forced == name) or (forced is None and name not in ("left", "ejected")
                                    and matches(self.state, conditions)):
                self.outcome = name
                return self.perform(variants, "ending", name)
        raise RuntimeError("No ending fits the world")

    def social_exchange(self, command):
        exchange = self.exchanges[command]
        # A performance cannot be farmed for relationship points by repeating it.
        if command in self.used_exchanges:
            return self.emit(Performance("already_said", (
                'Eli: "We heard you. Give us a moment to do something with it."',)),
                "reaction", command)
        score, reasons = 0, []
        for conditions, weight, reason in exchange.influences:
            if matches(self.state, conditions):
                score += weight
                reasons.append({"rule": reason, "weight": weight})
        willing = score >= exchange.threshold
        # Selection evidence is separate from story state and player-facing prose.
        self.selections.append({"turn": self.state["turn"], "exchange": command,
                                "score": score, "threshold": exchange.threshold,
                                "willing": willing, "rules": reasons})
        variants = exchange.variants if willing else (self.refusal(command),)
        selected = next(v for v in variants if matches(self.state, v.when))
        # Refused requests may be retried after changing state.
        if willing and selected.id != "not_needed":
            self.used_exchanges.add(command)
        return self.emit(selected, "exchange", command)

    def refusal(self, command):
        name = "Mara" if command.endswith("mara") else "Eli"
        person = name.lower()
        if command.startswith("reflect "):
            if not self.state["people"][person]["disclosed"]:
                line = name + ': "You don\'t know what I\'ve done. Ask me before you judge it."'
            elif self.state["people"][person]["memes"]["anger"] > 5:
                line = name + ': "I can\'t listen to this while I\'m this angry."'
            else:
                line = name + ': "After what you\'ve said, I don\'t trust you to be fair."'
        else:
            line = 'Mara: "Don\'t ask us to make a promise before we\'ve owned what happened."'
        return Performance("refused", (line,))

    @staticmethod
    def normalize(command):
        return re.sub(r"\s+", " ", command.strip().lower())

    def step(self, raw):
        command = self.normalize(raw)
        if self.outcome:
            return ["The evening is over. Start a new session to try another approach."]
        if not self.started:
            raise RuntimeError("Call start() before step()")
        if command not in self.actions():
            return ["That isn't a supported action. Type help for the available moves."]
        self.commands.append(command)
        # Input is also a trace event; replay can check the entire state chain.
        lines = self.emit(Performance(command, ("> " + command,),
                                     (("set", "turn", self.state["turn"] + 1),)),
                          "input", "player")
        if command == "leave":
            return lines + self.finish("left")
        if command == "provoke":
            count = self.state["people"]["player"]["insults"] + 1
            reaction = ('Mara: "You came here to watch us hurt each other? Stop."' if count == 1
                        else 'Eli: "That is enough. Get your coat."')
            lines += self.emit(Performance("boundary", (reaction,), (
                ("set", "people.player.insults", count),
                ("set", "people.player.caused_harm", True),
                ("add", "people.mara.memes.anger", 2),
                ("add", "people.eli.memes.anger", 2))), "exchange", command)
            if count >= 2:
                return lines + self.finish("ejected")
        elif command.startswith("ask "):
            topic = command.split()[1]
            tier = self.topic_tiers[topic]
            self.focus = topic
            if tier < len(self.mixins[topic]):
                lines += self.perform(self.mixins[topic][tier], "mixin", topic + "." + str(tier))
                if self.events[-1]["variant"] != "refused":
                    self.topic_tiers[topic] += 1
                # A joint exchange is atomic: interruptions happen between goals.
                self.interrupted = self.active is not None
                if self.state["turn"] >= 24:
                    return lines + self.finish()
                return lines
            lines += self.emit(Performance("exhausted", (
                'Mara: "There isn\'t another secret in that. It\'s what we do now that matters."',)),
                "reaction", topic)
        elif command != "listen":
            lines += self.social_exchange(command)
        # An earned agreement changes the remaining arc, not just its last line.
        if (self.active is not None and self.beats[self.active].phase in ("topics", "crisis")
                and self.phase() == "decision"):
            lines += self.emit(Performance("release", (
                "They let the unfinished argument drop. There is a smaller, more immediate decision to make.",)),
                "abort", self.active)
            self.aborted.append(self.active)
            self.active, self.cursor, self.interrupted = None, 0, False
        if self.state["turn"] >= 24:
            lines += self.emit(Performance("late", (
                "The candles have burned down. Mara reaches for the hall light.",)), "transition", "deadline")
            return lines + self.finish()
        return lines + self.advance()

    def actions(self):
        return {"listen": "Let the hosts continue.",
                **{"ask " + t: "Ask about the " + t + "." for t in self.mixins},
                **{key: value.label for key, value in self.exchanges.items()},
                "provoke": "Mock the hosts' relationship.", "leave": "Take your coat and leave."}

    def export(self):
        return {"schema": 1, "seed": self.seed, "commands": self.commands,
                "outcome": self.outcome, "state": self.snapshot(),
                "completed_beats": list(self.completed), "active_beat": self.active,
                "aborted_beats": list(self.aborted),
                "events": deepcopy(self.events), "decisions": deepcopy(self.selections),
                "transcript": list(self.transcript)}

    def save(self, path):
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(self.export(), stream, indent=2, ensure_ascii=False)
            stream.write("\n")


def replay(record):
    session = Session(record["seed"])
    session.start()
    for command in record["commands"]:
        session.step(command)
    return session
