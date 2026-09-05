import type { Dictionary } from "./dictionary";

/**
 * English homepage copy — a faithful translation of `vi-home.ts`, not new
 * marketing prose. Design-fixed strings ("ROOT FURTHER", "ABOUT AWARDS",
 * award category names, the event date/venue) stay identical to the VN
 * locale because they are brand copy, not prose to translate.
 */
export const enHome: Dictionary["home"] = {
  wordmarkAlt: "ROOT FURTHER",
  comingSoon: "Coming soon",
  days: "DAYS",
  hours: "HOURS",
  minutes: "MINUTES",
  eventTimeLabel: "Time:",
  eventTimeValue: "26/12/2025",
  eventVenueLabel: "Venue:",
  eventVenueValue: "Âu Cơ Art Center",
  eventLivestream: "Live broadcast via Livestream",
  ctaAwards: "ABOUT AWARDS",
  ctaKudos: "ABOUT KUDOS",
  rootFurther: {
    rootAlt: "ROOT",
    furtherAlt: "FURTHER",
    paragraphs: [
      `Facing the whirlwind changes of the AI era and ever-rising expectations from customers, Sun* has chosen a strategy of diversifying capabilities — not only to strive to become experts in our own fields, but to reach for something greater: a world where every Sunner is a "problem-solver", an expert at solving every problem and finding answers to every challenge facing projects, customers, and society.`,
      `Inspired by diverse capabilities, the ability to grow flexibly, and the spirit of digging deep to break through in the AI era, "Root Further" was chosen as the official theme of the Sun* Annual Awards 2025 ceremony.`,
      `Beyond its surface meaning, "Root Further" is the journey of reaching further, rooting deeper, and touching the hidden "geological layers" to keep existing, rising, and nurturing the ever-burning passion of Sun* people for creating value. Borrowing the image of roots driving ever deeper into the earth, weaving powerfully through layer after layer of "sediment" to absorb what is most essential, Sun* people are likewise "absorbing" nourishment from the era and the challenges of the market to renew themselves every day, expanding their capabilities and firmly "taking root" in the AI era — an entirely new "geological layer", complex and unpredictable, yet also gathering boundless potential and opportunity.`,
      `Before a storm, only trees with roots strong enough can stand firm. An organization built on individuals who are confident in their diverse capabilities, ready to create and embrace challenges, and to take charge of change is one that not only stays steady through upheaval, but also seizes every advantage and overcomes the challenges of the times. More than just the name of a new chapter in the organization's growth journey, "Root Further" is also a call to encourage each of us to dare to believe in ourselves, dare to dig deep, unlock every potential, dare to break our limits, and dare to become the most versatile and excellent version of ourselves. Because in the AI era, diversifying capabilities and harnessing the strength of the times are the prerequisites for lasting far into the future.`,
      `No one knows in advance how many mysterious "geological layers" still lie hidden in the "earth" of today's technology industry and market. All we know is that once "Root Further" becomes our rooted spirit, we will no longer fear it — instead we will grow more eager for whatever uncharted territory lies ahead on our path forward. Because we always believe that within those very boundless frontiers lie countless wonders and opportunities for us to rise and grow.`,
    ],
    quote: "A tree with deep roots fears no storm",
    quoteSource: "(English proverb)",
  },
  awards: {
    eyebrow: "Sun* annual awards 2025",
    title: "Award System",
    detailLabel: "Details",
    cards: {
      topTalent: {
        title: "Top Talent",
        description: "Honoring top individuals who excel in every dimension",
      },
      topProject: {
        title: "Top Project",
        description:
          "Honoring outstanding projects in every dimension, with standout revenue performance",
      },
      topProjectLeader: {
        title: "Top Project Leader",
        description: "Honoring managers who inspire and lead breakthrough projects.",
      },
      bestManager: {
        title: "Best Manager",
        description: "Honoring managers with strong management skills who lead their teams well",
      },
      signature2025Creator: {
        title: "Signature 2025 - Creator",
        description: "Honoring managers with strong management skills who lead their teams well",
      },
      mvp: {
        title: "MVP (Most Valuable Person)",
        description: "Honoring managers with strong management skills who lead their teams well",
      },
    },
  },
  kudos: {
    eyebrow: "Recognition movement",
    title: "Sun* Kudos",
    subtitle: "WHAT'S NEW IN SAA 2025",
    body: "A recognition and appreciation initiative — running for the first time for every Sunner. It launches in November 2025, encouraging Sun* people to share words of recognition and thanks for their colleagues on the platform announced by the Organizing Committee. This will be the material the Heads Council references when selecting award winners.",
    cta: "Details",
  },
  widget: {
    writeKudos: "Write kudos",
    standards: "SAA standards",
  },
};
