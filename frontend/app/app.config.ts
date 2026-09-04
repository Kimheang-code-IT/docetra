export default defineAppConfig({
  ui: {
    colors: {
      primary: 'brand',
      secondary: 'navy',
      neutral: 'zinc',
    },

    /** Route top-bar / toast progress / loaders follow brand primary. */
    progress: {
      defaultVariants: {
        color: 'primary',
        size: 'sm',
        animation: 'carousel',
      },
    },

    toast: {
      defaultVariants: {
        color: 'primary',
      },
    },

    /**
     * ERPNext-style form controls:
     * soft elevated fill with no border when idle;
     * grey inset ring only when focused / open.
     */
    formField: {
      slots: {
        label: 'block text-sm font-medium text-toned',
        help: 'mt-1.5 text-xs text-muted leading-relaxed',
        error: 'mt-1.5 text-xs text-error',
        hint: 'text-xs text-muted',
        description: 'text-xs text-muted',
      },
    },

    input: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated focus:bg-elevated ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    textarea: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated focus:bg-elevated ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    select: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated focus:bg-elevated data-[state=open]:bg-elevated ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default data-[state=open]:ring-1 data-[state=open]:ring-inset data-[state=open]:ring-default focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    selectMenu: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated focus:bg-elevated data-[state=open]:bg-elevated ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default data-[state=open]:ring-1 data-[state=open]:ring-inset data-[state=open]:ring-default focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    inputMenu: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated focus:bg-elevated data-[state=open]:bg-elevated ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default data-[state=open]:ring-1 data-[state=open]:ring-inset data-[state=open]:ring-default focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    inputNumber: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated focus:bg-elevated ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    inputDate: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated has-focus:bg-elevated ring-0 shadow-none outline-none has-focus:ring-1 has-focus:ring-inset has-focus:ring-default has-focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'outline-none shadow-none ring-0 has-focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    inputTime: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated has-focus:bg-elevated ring-0 shadow-none outline-none has-focus:ring-1 has-focus:ring-inset has-focus:ring-default has-focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      compoundVariants: [
        {
          color: 'neutral',
          variant: ['soft', 'ghost'],
          class: 'outline-none shadow-none ring-0 has-focus-visible:outline-none',
        },
      ],
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    pinInput: {
      variants: {
        variant: {
          soft: 'text-highlighted bg-elevated/70 hover:bg-elevated focus:bg-elevated ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default focus-visible:outline-none disabled:bg-elevated/50',
        },
      },
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'soft',
      },
    },

    /** Checked state uses inverted (near-black) fill like the document form screenshot. */
    checkbox: {
      defaultVariants: {
        size: 'md',
        color: 'neutral',
        variant: 'list',
        indicator: 'start',
      },
    },

    switch: {
      defaultVariants: {
        size: 'md',
        color: 'neutral',
      },
    },

    /** Keep every horizontal tab group anchored to the left. */
    tabs: {
      slots: {
        root: 'items-start',
        list: 'justify-start',
      },
    },

    dashboardPanel: {
      slots: {
        // Keep main content inset consistent (reload + navigate)
        body: 'flex flex-col gap-0 flex-1 overflow-y-auto px-1.5 pt-1.5 pb-0',
      },
    },
    dashboardNavbar: {
      slots: {
        root: 'h-(--ui-header-height) shrink-0 flex items-center justify-between border-b border-default px-1.5 gap-1.5',
      },
    },
    modal: {
      compoundVariants: [
        {
          scrollable: true,
          fullscreen: false,
          class: {
            overlay: 'grid !place-items-start !justify-items-center p-4 !pt-[5vh] sm:!pt-[5vh]',
          },
        },
        {
          scrollable: false,
          fullscreen: false,
          class: {
            // Override default vertical center (top-1/2 -translate-y-1/2)
            content: '!top-[5%] left-1/2 !-translate-x-1/2 !translate-y-0 max-h-[calc(100dvh-8vh)] sm:max-h-[calc(100dvh-10vh)] overflow-hidden',
          },
        },
      ],
    },
  },
})
