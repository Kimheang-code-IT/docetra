export default defineAppConfig({
  ui: {
    colors: {
      primary: 'brand',
      secondary: 'navy',
      neutral: 'zinc',
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
