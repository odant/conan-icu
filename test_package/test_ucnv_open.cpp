/*
 * ICU Conan package
 * Test for ::ucnv_open (debug static build)
 * Dmitriy Vetutnev, ODANT 2020
*/


#include <unicode/ucnv.h>

#include <cassert>
#include <cstdlib>


int main(int, char**) {

    UErrorCode status = U_ZERO_ERROR;

    UConverter *conv = ::ucnv_open("cp1251", &status);

    assert(conv != nullptr);
    assert(U_SUCCESS(status));

    ::ucnv_close(conv);

    return EXIT_SUCCESS;
}
