"""Reusable scene meanings with bound participants and shared reading claims.

World plans choose the meaning and its grounded arguments. Grammar subclasses
can give a family more realizations without changing those plans or QA facts.
"""
class SceneFamilies:
    def say_intent(self, speaker, verb, content, *, listener=None):
        if verb not in {"want", "promise", "choose"}:
            raise ValueError("unsupported speech intention")
        return self.line(speaker, self.me(self.v(verb, content)), listener=listener)

    def ability(self, speaker, action, *, listener=None):
        return self.line(speaker, self.me(self.can(action)), listener=listener)

    def offer(self, speaker, action, *, listener=None):
        """An offer of an action, distinguished from a bare ability statement."""
        return self.ability(speaker, action, listener=listener)

    def transfer(self, actor, recipient, item):
        return self.s(actor, self.v("give", recipient, item))

    def fetch_scene(self, actor, item, source, *, then=None, claim_key="tool"):
        from .surface import claim, scene
        e = self.world.entities
        action = self.adv(self.v("fetch", self.ref(item)), self.pp("from", self.n(source)))
        sentence = self.sequence(actor, action, then) if then is not None else self.s(actor, action)
        # The same role bindings drive both text and the answer. This family
        # only runs when the world's guarded fetch event has been offered.
        return scene(sentence, qa=[claim(claim_key, "where",
            f"Where did the {e[item].noun} come from?",
            f"{e[actor].noun} fetched the {e[item].noun} from the {source}.", actor, item)])
