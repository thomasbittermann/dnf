INSTALL (FILES "collect_dnf.conf" DESTINATION ${SYSCONFDIR}/libreport/events.d/)
ADD_SUBDIRECTORY (dnf)
ADD_SUBDIRECTORY (systemd)
ADD_SUBDIRECTORY (bash_completion.d)
