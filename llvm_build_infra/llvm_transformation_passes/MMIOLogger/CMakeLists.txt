add_library(MMIOLogger MODULE src/MMIOLoggerPass.cpp src/MemAccessFetcher.cpp include/MemAccessFetcher.h)

include_directories(include)

target_compile_features(MMIOLogger PRIVATE cxx_range_for cxx_auto_type)

set_target_properties(MMIOLogger PROPERTIES
        COMPILE_FLAGS "-g"
        )

if(APPLE)
    set_target_properties(MMIOLogger PROPERTIES
            LINK_FLAGS "-undefined dynamic_lookup"
            )
endif(APPLE)
