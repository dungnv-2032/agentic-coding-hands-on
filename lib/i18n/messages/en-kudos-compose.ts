import type { Dictionary } from "./dictionary";

/**
 * English Viết Kudo compose copy, typed against the shared
 * `Dictionary["kudosCompose"]` shape so a key missing here fails
 * `npm run typecheck`. A faithful translation of `vi-kudos-compose.ts`; vi
 * is authoritative and no test asserts EN copy. `labels.hashtag` and
 * `labels.image` stay unchanged — the design renders those labels in
 * English in both locales, same convention as `header.kudos: "Sun* Kudos"`
 * in `dictionary.ts`.
 */
export const enKudosCompose: Dictionary["kudosCompose"] = {
  title: "Send thanks and recognition to a teammate",
  labels: {
    recipient: "Recipient",
    title: "Title",
    body: "Message",
    hashtag: "Hashtag",
    image: "Image",
  },
  placeholders: {
    recipient: "Search",
    title: "Give your teammate a title",
    body: "Share your thanks and recognition with your teammate here!",
    anonymousName: "Enter the name you'd like to show",
  },
  hints: {
    titleLine1: "Example: The person who motivates me.",
    titleLine2: "This title will appear as your Kudos headline.",
    body: 'You can use "@ + name" to mention a colleague',
  },
  buttons: {
    addHashtag: "+ Hashtag",
    addImage: "+ Image",
    max: "Max 5",
    cancel: "Cancel",
    submit: "Send",
  },
  toolbar: {
    bold: "Bold",
    italic: "Italic",
    strike: "Strikethrough",
    orderedList: "Ordered list",
    link: "Link",
    quote: "Quote",
  },
  // Addlink Box (OyDLDuSGEa) — en takes spec item A/B/C/D's own English naming
  // ("Add link"/"Text"/"URL"/"Save"), per clarifications.md § Copy for the two locales.
  linkDialog: {
    heading: "Add link",
    textLabel: "Text",
    urlLabel: "URL",
    confirm: "Save",
    // Unauthored — the frame carries no error state.
    errors: {
      required: "This field is required",
      tooShort: "URL is too short",
      tooLong: "This exceeds the maximum length",
      invalidUrl: "Enter a valid URL",
    },
  },
  errors: {
    required: "This field is required",
    tooMany: "Maximum 5 hashtags",
    invalidType: "This file format isn't supported",
    unknown: "Something went wrong. Please try again.",
  },
  recipientEmpty: "No matching people found.",
  communityStandards: "Community standards",
  anonymousCheckboxLabel: "Send this Kudos anonymously",
  anonymousNameLabel: "Anonymous display name",
  submitPending: "Sending...",
  anonymousFallbackName: "Anonymous",
};
