"use client";

import { useActionState, useCallback, useEffect, useReducer, useRef, useState } from "react";

import type { Dictionary } from "@/lib/i18n/dictionaries";
import type { ComposeOptionsView, CreateKudos, UploadKudosImage } from "@/lib/kudos/compose-contract";
import { buildPayload, composeReducer, createInitialComposeState, isSubmitReady } from "@/lib/kudos/compose-state";
import { validateCompose } from "@/lib/kudos/validate-compose";

import { AnonymousToggle } from "./anonymous-toggle";
import { ComposeActions } from "./compose-actions";
import { ComposeField } from "./compose-field";
import { FieldRow, mergeErrors } from "./compose-form-helpers";
import { buildHashtagPickerCopy, HashtagPicker } from "./hashtag-picker";
import { buildImagePickerCopy, ImagePicker } from "./image-picker";
import { KudosBodyEditor } from "./kudos-body-editor";
import { RecipientPicker } from "./recipient-picker";
import { TitleField } from "./title-field";
import { useBodyEditorController } from "./use-body-editor-controller";

/** Hủy never asks a "leave without saving?" question (clarifications.md § Validation). */
const CANCEL_HREF = "/kudos";

export interface ComposeFormProps {
  copy: Dictionary["kudosCompose"];
  options: ComposeOptionsView;
  createKudos: CreateKudos;
  uploadKudosImage: UploadKudosImage;
}

/**
 * mm:520:11647 — "Viết KUDO" modal, re-measured live: `752×1012px`, `padding: 40px`,
 * `gap: 32px`, `radius: 24px`, `bg: #FFF8E1` (`get_node`, matches design-source-analysis.md
 * § 8). `Content` (`mm:…;520:9874`) groups body+hashtags+images with its own `gap: 24px`.
 * Field order below is confirmed by `get_overview`'s live childIds: title → recipient →
 * Danh hiệu → Content → anonymous → footer.
 *
 * Single client boundary owning the whole compose state (`compose-state.ts`, frozen) —
 * every child is presentational, reporting upward only, same discipline as `kudos-board.tsx`.
 * `useActionState` submits a typed `ComposePayload`, not `FormData` (Key Insight 4,
 * `forms.md:190-274`): `submit` is called imperatively from `handleSubmit`, itself the
 * `<form action>` so no native navigation fires — `pending` still tracks it.
 */
export function ComposeForm({ copy, options, createKudos, uploadKudosImage }: ComposeFormProps) {
  const [state, dispatch] = useReducer(composeReducer, createInitialComposeState());
  const [actionState, submit, pending] = useActionState(createKudos, { errors: {} });
  const [recipientQuery, setRecipientQuery] = useState("");
  const [awaitingUploads, setAwaitingUploads] = useState(false);
  const bodyController = useBodyEditorController(state, dispatch, options.recipients);

  const serverErrors = "errors" in actionState ? actionState.errors : {};
  const errors = mergeErrors(state.errors, serverErrors);
  const submitReady = isSubmitReady(state);

  // `stateRef` mirrors `state` for `handleSubmit`'s wait loop below, which
  // must read the LATEST images (resolved by `ImagePicker`'s own async
  // upload calls) rather than the stale snapshot closed over at click time.
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const handleSubmit = useCallback(async () => {
    if (pending || awaitingUploads) return;
    // Insight 3: an image whose upload hasn't resolved yet (`imageUrl ===
    // null`) must be awaited, never silently dropped from the payload.
    if (stateRef.current.images.some((image) => image.imageUrl === null)) {
      setAwaitingUploads(true);
      while (stateRef.current.images.some((image) => image.imageUrl === null)) {
        await new Promise((resolve) => setTimeout(resolve, 50));
      }
      setAwaitingUploads(false);
    }
    const payload = buildPayload(stateRef.current);
    const fieldErrors = validateCompose(payload);
    if (Object.keys(fieldErrors).length > 0) {
      dispatch({ type: "setErrors", errors: fieldErrors });
      return;
    }
    submit(payload);
  }, [pending, awaitingUploads, submit]);

  return (
    <div className="flex w-full flex-1 items-center justify-center px-6 py-16">
      {/* mm:520:11647 */}
      <form
        data-testid="compose-form"
        action={handleSubmit}
        className="flex w-full max-w-[752px] flex-col items-start gap-8 rounded-3xl bg-[#FFF8E1] p-10"
      >
        {/* mm:I520:11647;520:9870 */}
        <h1 className="w-full text-center text-[32px] leading-10 font-bold text-[#00101A]">{copy.title}</h1>

        <FieldRow label={copy.labels.recipient} required>
          <RecipientPicker
            copy={{ placeholder: copy.placeholders.recipient, emptyLabel: copy.recipientEmpty }}
            options={options.recipients}
            value={state.recipient}
            query={recipientQuery}
            error={errors.recipient}
            onQueryChange={(query) => {
              setRecipientQuery(query);
              dispatch({ type: "setRecipient", recipient: null });
            }}
            onSelect={(option) => {
              dispatch({ type: "setRecipient", recipient: option });
              setRecipientQuery(option.fullName);
            }}
          />
          <ComposeField field="recipient" error={errors.recipient} copy={copy.errors} />
        </FieldRow>

        <FieldRow label={copy.labels.title} required>
          <TitleField
            copy={{
              placeholder: copy.placeholders.title,
              hintExample: copy.hints.titleLine1,
              hintUsage: copy.hints.titleLine2,
            }}
            value={state.title}
            error={errors.title}
            onChange={(title) => dispatch({ type: "setTitle", title })}
          />
          <ComposeField field="title" error={errors.title} copy={copy.errors} />
        </FieldRow>

        {/* mm:I520:11647;520:9874 — Content, gap 24px */}
        <div className="flex w-full flex-col gap-6">
          <div>
            <KudosBodyEditor
              copy={{
                placeholder: copy.placeholders.body,
                hint: copy.hints.body,
                communityStandardsLabel: copy.communityStandards,
                toolbar: copy.toolbar,
                linkDialog: copy.linkDialog,
                cancelLabel: copy.buttons.cancel,
              }}
              text={state.body.text}
              error={errors.body}
              {...bodyController}
            />
            <ComposeField field="body" error={errors.body} copy={copy.errors} />
          </div>

          <FieldRow label={copy.labels.hashtag} required>
            <HashtagPicker
              copy={buildHashtagPickerCopy(copy)}
              options={options.hashtags}
              selected={state.hashtags}
              error={state.hashtagError}
              onAdd={(hashtag) => dispatch({ type: "addHashtag", hashtag })}
              onRemove={(id) => dispatch({ type: "removeHashtag", id })}
            />
            <ComposeField field="hashtag" error={errors.hashtag} copy={copy.errors} />
          </FieldRow>

          <FieldRow label={copy.labels.image}>
            <ImagePicker
              copy={buildImagePickerCopy(copy)}
              images={state.images}
              error={state.imageError}
              uploadImage={uploadKudosImage}
              onAdd={(image) => dispatch({ type: "addImage", image })}
              onResolve={(id, imageUrl) => dispatch({ type: "resolveImage", id, imageUrl })}
              onRemove={(id) => dispatch({ type: "removeImage", id })}
              onError={(error) => dispatch({ type: "setImageError", error })}
            />
          </FieldRow>
        </div>

        <AnonymousToggle
          copy={{ checkboxLabel: copy.anonymousCheckboxLabel, nameInputLabel: copy.anonymousNameLabel }}
          checked={state.isAnonymous}
          name={state.anonymousName}
          onToggle={(anonymous) => dispatch({ type: "setAnonymous", anonymous })}
          onNameChange={(name) => dispatch({ type: "setAnonymousName", name })}
        />

        <ComposeActions
          copy={{
            cancelLabel: copy.buttons.cancel,
            submitLabel: copy.buttons.submit,
            submitPendingLabel: copy.submitPending,
          }}
          cancelHref={CANCEL_HREF}
          submitReady={submitReady}
          pending={pending || awaitingUploads}
        />
      </form>
    </div>
  );
}
