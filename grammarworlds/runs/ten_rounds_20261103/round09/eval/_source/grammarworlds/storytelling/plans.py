"""Short semantic realizations, composed from typed phrases rather than stories.

None means an internal physical step. Those steps still execute, guard, and
replay; later scenes can aggregate only effects already recorded in that world.
"""
from .surface import SpeechLanguage, scene, claim
from ..portable.nouns import pronoun


def plan(w, f, tense="past", lexicon=None):
    g = SpeechLanguage(w, tense, lexicon)
    from .rescue_plans import rescue
    from .kite_plans import kite
    from .key_plans import key
    from .music_plans import music
    from .greenhouse_plans import greenhouse
    dispatch = {"rescue": rescue, "kite": kite, "key": key,
                "music": music, "greenhouse": greenhouse, "library": library, "pottery": pottery}
    return dispatch[w.scenario](w, f, g)


def library(w, f, g):
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    if f.kind == "wish":
        return scene(g.sequence("hero", v("hold", r("atlas", first=True)),
                                v("want", v("sketch", n("moon")))), qa=[
            claim("goal", "what", "What did Mina want to do?", "Mina wanted to sketch the moon. She held a moon atlas.", "hero", "atlas")])
    if f.kind == "missing":
        return scene(g.line("friend", s(g.possess(pronoun("I"), g.cn("whale book")), g.be("missing"), tense="present"), listener="hero"),
                     g.line("hero", g.me(v("promise", v("help", pronoun("you")))), listener="friend"), qa=[
            claim("promise", "who", "Who promised to help Jun?", "Mina promised to help Jun. Jun had said his whale book was missing.", "hero", "friend", "book")])
    if f.kind == "failed_search":
        return scene(g.join(s(g.both(r("hero"), r("friend")), v("search", n("window nook"))),
                            s("hero", v("find", r("book")), negative=True), "but"), qa=[
            claim("failed_search", "where", "Where did the children search without finding the book?", "They did not find the book in the window nook. Mina and Jun searched there together.", "hero", "friend", "book")])
    if f.kind == "clue":
        return scene(g.either(s("friend", g.adv(v("spot", r("bookmark")), pp("on", n("high shelf")))),
                              s("friend", g.adv(v("see", r("bookmark")), pp("on", n("high shelf"))))), qa=[
            claim("clue", "what", "What clue did Jun spot?", "Jun spotted a star bookmark. It was on a high shelf.", "friend", "bookmark")])
    if f.kind == "reserve_atlas":
        return scene(s("helper", g.adv(v("save", r("atlas")), pp("for", r("hero")))), qa=[
            claim("atlas", "who", "Who saved the atlas for Mina?", "Ms Alvarez saved the moon atlas for Mina.", "helper", "atlas", "hero")])
    if f.kind == "release_atlas":
        return scene(g.sequence("hero", g.adv(v("return", r("atlas")), pp("to", n("display table"))),
                                v("choose", v("help", r("friend")))) , qa=[
            claim("atlas", "why", "Why did Mina put her atlas back?", "Mina chose to help Jun. She returned the atlas to the display table.", "hero", "friend", "atlas")])
    if f.kind == "retrieve":
        return scene(g.using("helper", g.adv(v("lift", r("book")), "down"), r("ladder")), qa=[
            claim("retrieve", "how", "How did they get the whale book down?", "Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf.", "helper", "book", "ladder", supports=("clue",))])
    if f.kind == "checkout":
        return scene(s("helper", v("give", r("friend"), r("book"))))
    if f.kind == "checkout_atlas":
        return None
    if f.kind in {"share_picture","share_atlas"}:
        source = "book" if f.kind == "share_picture" else "atlas"
        subject = "whale" if source == "book" else "moon"
        return scene(g.line("friend",g.me(g.can(v("help",pronoun("you")))),listener="hero"),
                     s("friend",g.adv(v("open",r(source)),pp("for",r("hero")))),qa=[
            claim("invitation","who","How did Jun help Mina with her drawing?",
                  f"Jun opened the {w.entities[source].noun} for Mina. She had helped him find his missing book.",
                  "hero","friend",source,supports=("promise","retrieve"))])
    if f.kind in {"sketch_moon","sketch_whale"}:
        subject = "moon" if f.kind == "sketch_moon" else "whale"
        source = "atlas" if subject == "moon" else "book"
        return scene(s("hero",g.adv(v("sketch",n(subject)),pp("from",r(source)),pp("on",r("paper")))),qa=[
            claim("drawing","how","What did Mina draw, and where did she find it?",f"Mina sketched the {subject} from the {w.entities[source].noun} on her paper.","hero","paper",source)])
    if f.kind == "ending":
        subject = "moon" if "atlas_reserved" in w.flags else "whale"
        answer = ("Mina showed Jun her moon drawing. Ms Alvarez had saved the atlas for her." if subject == "moon" else
                  "Mina showed Jun her whale drawing. She had put the moon atlas back, and Jun had opened his whale book for her.")
        supports = ("drawing","atlas","invitation")
        return scene(s("hero",v("show",r("friend"),r("paper",adjectives=(subject,)))),qa=[
            claim("outcome","what_next","How did Mina's drawing plan turn out?",answer,"hero","friend","paper",supports=supports)])
    return None


def pottery(w, f, g):
    n, r, v, s, pp = g.n, g.ref, g.v, g.s, g.pp
    cup = r("cup")
    if f.kind == "need":
        return None  # The following goal scene states the grip problem and its consequence together.
    if f.kind == "goal":
        return scene(g.line("hero", g.me(v("want", v("give", r("grandpa"), n("cup", det="a")))), listener="helper"),
                     g.join(s(g.possess(cup, g.cn("handle")), g.be("wide")),
                            s(g.possess(r("grandpa"), g.cn("hand")), g.be("stiff")), "because"), qa=[
            claim("gift", "who", "Who was Bea making the cup for?", "Bea was making the cup for Grandpa Len.", "hero", "grandpa", "cup"),
            claim("grip_reason", "why", "Why did the cup have a wide handle?", "Grandpa Len's hand was stiff. The cup had a wide handle for him.", "grandpa", "cup")])
    if f.kind == "slip":
        return scene(g.join(s(r("tool"), v("slip")), s(cup, g.be("dented"))), qa=[
            claim("accident", "what", "What happened when the shaping rib slipped?", "The cup was dented when the shaping rib slipped.", "tool", "cup")])
    if f.kind == "inspect":
        return scene(g.line("helper", s(g.possess(cup, g.cn("wall")), g.be("thick"), tense="present"), listener="hero"), qa=[
            claim("inspection", "what", "What did Mr Ivo say about the cup's wall?", "Mr Ivo said the cup's wall was thick.", "helper", "hero", "cup")])
    if f.kind == "consult":
        return scene(g.line("grandpa",g.me(g.can(g.adv(v("hold",n("bowl",det="a")),pp("with",g.counted(2,"hand"))))),listener="hero"),qa=[
            claim("consultation","how","What did Grandpa Len say he could hold?","Grandpa Len said he could hold a bowl with two hands.","grandpa","cup")])
    if f.kind == "remake":
        return scene(g.line("hero",g.me(v("want",n("bowl",det="a"))),listener="helper"),
                     g.using("hero",g.adv(v("reshape",cup),pp("into",n("bowl",det="a"))),r("tool")),qa=[
            claim("design","how","How did Bea change her gift design?","Bea reshaped the cup into a bowl with the shaping rib. Grandpa Len had said he could hold a bowl with two hands.","hero","grandpa","cup","tool",supports=("inspection","consultation"))])
    if f.kind == "thumb":
        return scene(g.line("hero", g.me(v("want", n("thumb rest", det="a"))), listener="helper"),
                     g.using("hero", g.adv(v("shape", n("dent")), pp("into", n("thumb rest", det="a"))), r("sponge")), qa=[
            claim("design", "how", "How did Bea use the dent after Mr Ivo checked the cup?", "Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick.", "hero", "cup", "sponge", supports=("inspection",))])
    if f.kind == "smooth":
        return scene(g.line("hero", g.me(v("want", v("smooth", n("dent")))), listener="helper"),
                     g.using("hero", v("smooth", n("dent")), r("sponge")), qa=[
            claim("design", "how", "How did Bea change the dent after Mr Ivo checked the cup?", "Bea smoothed the dent with the sponge. Mr Ivo had said the cup's wall was thick.", "hero", "cup", "sponge", supports=("inspection",))])
    if f.kind == "deliver":
        assert {"fired", "cool", "glazed"} <= w.entities["cup"].state
        # The two firings and glaze are all completed trace events, not predicted effects.
        assert {"bisque", "glaze", "fire"} <= {x["frame"]["kind"] for x in w.history}
        return scene(s("helper", g.adv(v("fire", cup), "twice")),
                     s(cup, g.be("cool")), qa=[
            claim("firing", "who", f"Who fired the {w.entities['cup'].noun}?", f"Mr Ivo fired the {w.entities['cup'].noun} twice. It was cool afterward.", "helper", "cup")])
    if f.kind == "give":
        return scene(s("hero", v("give", r("grandpa"), cup)))
    if f.kind == "use":
        return scene(s("grandpa", g.adv(v("pour", n("tea", det="bare")), pp("into", cup))), qa=[
            claim("tea", "what", f"What did Grandpa Len put in the {w.entities['cup'].noun}?", f"Grandpa Len poured tea into the {w.entities['cup'].noun}.", "grandpa", "cup")])
    if f.kind == "ending":
        if "bowl_design" in w.flags:
            return scene(s("grandpa",g.adv(v("hold",cup),pp("with",g.counted(2,"hand")))),qa=[
                claim("outcome","what_next","What did Grandpa Len do with the bowl at the end?","Grandpa Len held the bowl with two hands. Bea had reshaped her cup into the bowl.","grandpa","hero","cup",supports=("design",))])
        if "thumb_design" in w.flags:
            return scene(s(g.possess(r("grandpa"), g.cn("thumb")), g.adv(v("rest"), pp("in", n("thumb rest")))), qa=[
                claim("outcome", "where", "Where did Grandpa Len rest his thumb?", "Grandpa Len rested his thumb in the thumb rest. Bea had shaped the dent into that thumb rest.", "grandpa", "cup", supports=("design",))])
        return scene(s("grandpa", v("hold", g.possess(cup, g.cn("handle", "wide")))), qa=[
            claim("outcome", "what_next", "How did Grandpa Len hold the cup at the end?", "Grandpa Len held the cup's wide handle. Bea had made the cup for him because his hand was stiff.", "grandpa", "cup", supports=("gift", "grip_reason"))])
    return None
