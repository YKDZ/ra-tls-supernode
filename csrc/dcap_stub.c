#include <stdint.h>
#include <stdio.h>
#include <time.h>

uint32_t sgx_qv_verify_quote(
    const uint8_t *p_quote,
    uint32_t quote_size,
    const void *p_quote_collateral,
    const time_t expiration_check_date,
    uint32_t *p_collateral_expiration_status,
    uint32_t *p_quote_verification_result,
    void *p_qve_report_info,
    uint32_t supplemental_data_size,
    uint8_t *p_supplemental_data) {
    printf("sgx_qv_verify_quote invoked\n");
    if (p_quote == NULL || quote_size == 0) {
        return 1; /* simulate failure */
    }
    *p_collateral_expiration_status = 0;
    *p_quote_verification_result = 0;
    return 0; /* success */
}

uint32_t sgx_qv_get_quote_supplemental_data_size(uint32_t *p_data_size) {
    printf("sgx_qv_get_quote_supplemental_data_size invoked\n");
    if (p_data_size == NULL) {
        return 1;
    }
    *p_data_size = 0;
    return 0;
}
