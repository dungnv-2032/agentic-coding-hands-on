export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      board_stats: {
        Row: {
          id: number
          spotlight_kudos_total: number
        }
        Insert: {
          id?: number
          spotlight_kudos_total?: number
        }
        Update: {
          id?: number
          spotlight_kudos_total?: number
        }
        Relationships: []
      }
      departments: {
        Row: {
          filter_position: number | null
          id: number
          name: string
        }
        Insert: {
          filter_position?: number | null
          id?: never
          name: string
        }
        Update: {
          filter_position?: number | null
          id?: never
          name?: string
        }
        Relationships: []
      }
      gift_awards: {
        Row: {
          awarded_at: string
          gift_label: string
          id: number
          sunner_id: number
        }
        Insert: {
          awarded_at: string
          gift_label: string
          id?: never
          sunner_id: number
        }
        Update: {
          awarded_at?: string
          gift_label?: string
          id?: never
          sunner_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "gift_awards_sunner_id_fkey"
            columns: ["sunner_id"]
            isOneToOne: false
            referencedRelation: "sunners"
            referencedColumns: ["id"]
          },
        ]
      }
      hashtags: {
        Row: {
          id: number
          name: string
          position: number
        }
        Insert: {
          id?: never
          name: string
          position: number
        }
        Update: {
          id?: never
          name?: string
          position?: number
        }
        Relationships: []
      }
      kudos: {
        Row: {
          anonymous_name: string | null
          campaign: string | null
          heart_baseline: number
          id: number
          is_anonymous: boolean
          message: string
          message_format: string
          receiver_id: number
          sender_id: number
          sent_at: string
        }
        Insert: {
          anonymous_name?: string | null
          campaign?: string | null
          heart_baseline?: number
          id?: never
          is_anonymous?: boolean
          message: string
          message_format?: string
          receiver_id: number
          sender_id: number
          sent_at: string
        }
        Update: {
          anonymous_name?: string | null
          campaign?: string | null
          heart_baseline?: number
          id?: never
          is_anonymous?: boolean
          message?: string
          message_format?: string
          receiver_id?: number
          sender_id?: number
          sent_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "kudos_receiver_id_fkey"
            columns: ["receiver_id"]
            isOneToOne: false
            referencedRelation: "sunners"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_sender_id_fkey"
            columns: ["sender_id"]
            isOneToOne: false
            referencedRelation: "sunners"
            referencedColumns: ["id"]
          },
        ]
      }
      kudos_attachments: {
        Row: {
          id: number
          image_url: string
          kudos_id: number
          position: number
        }
        Insert: {
          id?: never
          image_url: string
          kudos_id: number
          position: number
        }
        Update: {
          id?: never
          image_url?: string
          kudos_id?: number
          position?: number
        }
        Relationships: [
          {
            foreignKeyName: "kudos_attachments_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "kudos"
            referencedColumns: ["id"]
          },
        ]
      }
      kudos_hashtags: {
        Row: {
          hashtag_id: number
          kudos_id: number
          position: number
        }
        Insert: {
          hashtag_id: number
          kudos_id: number
          position: number
        }
        Update: {
          hashtag_id?: number
          kudos_id?: number
          position?: number
        }
        Relationships: [
          {
            foreignKeyName: "kudos_hashtags_hashtag_id_fkey"
            columns: ["hashtag_id"]
            isOneToOne: false
            referencedRelation: "hashtags"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "kudos_hashtags_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "kudos"
            referencedColumns: ["id"]
          },
        ]
      }
      kudos_likes: {
        Row: {
          created_at: string
          id: number
          kudos_id: number
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: never
          kudos_id: number
          user_id: string
        }
        Update: {
          created_at?: string
          id?: never
          kudos_id?: number
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "kudos_likes_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "kudos"
            referencedColumns: ["id"]
          },
        ]
      }
      spotlight_ticker_events: {
        Row: {
          id: number
          kudos_id: number
          occurred_at: string
          sunner_id: number
        }
        Insert: {
          id?: never
          kudos_id: number
          occurred_at: string
          sunner_id: number
        }
        Update: {
          id?: never
          kudos_id?: number
          occurred_at?: string
          sunner_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "spotlight_ticker_events_kudos_id_fkey"
            columns: ["kudos_id"]
            isOneToOne: false
            referencedRelation: "kudos"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "spotlight_ticker_events_sunner_id_fkey"
            columns: ["sunner_id"]
            isOneToOne: false
            referencedRelation: "sunners"
            referencedColumns: ["id"]
          },
        ]
      }
      sunners: {
        Row: {
          auth_user_id: string | null
          avatar_url: string
          department_id: number
          full_name: string
          id: number
          kudos_received_baseline: number
          secret_box_opened_count: number
          secret_box_unopened_count: number
        }
        Insert: {
          auth_user_id?: string | null
          avatar_url: string
          department_id: number
          full_name: string
          id?: never
          kudos_received_baseline?: number
          secret_box_opened_count?: number
          secret_box_unopened_count?: number
        }
        Update: {
          auth_user_id?: string | null
          avatar_url?: string
          department_id?: number
          full_name?: string
          id?: never
          kudos_received_baseline?: number
          secret_box_opened_count?: number
          secret_box_unopened_count?: number
        }
        Relationships: [
          {
            foreignKeyName: "sunners_department_id_fkey"
            columns: ["department_id"]
            isOneToOne: false
            referencedRelation: "departments"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      create_kudos: {
        Args: {
          p_anonymous_name: string
          p_campaign: string
          p_hashtag_ids: number[]
          p_image_urls: string[]
          p_is_anonymous: boolean
          p_message: string
          p_message_format: string
          p_receiver_id: number
        }
        Returns: number
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const

